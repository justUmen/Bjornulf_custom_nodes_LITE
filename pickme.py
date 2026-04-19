import os
import json
import threading
from aiohttp import web
from server import PromptServer
import logging

SAVE_PATH = os.path.join("Bjornulf", "pickme_groups.json")
active_nodes = set()
lock = threading.Lock()

def normalize_group(name):
    return name.strip().lower()

def load_groups():
    try:
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading groups: {e}")
        return {}

def save_groups(groups):
    try:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(groups, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Error saving groups: {e}")

def remove_txt(group_name):
    logging.info(f"remove_txt {group_name} !!!!")
    file_path = os.path.join("Bjornulf", "pickme", f"{group_name}.txt")
    try:
        with open(file_path, "w") as f:
            f.truncate(0)
    except Exception as e:
        print(f"Error emptying text file for group '{group_name}': {e}")

def empty_groups():
    logging.info(f"empty_groups !!!!")
    try:
        with open(SAVE_PATH, "w") as f:
            f.write("")  # Write an empty JSON object
            # f.write("{}")  # Write an empty JSON object
        print("File emptied successfully.")
    except Exception as e:
        print(f"Error emptying file: {e}")

# The cleanup_groups function now checks against the active_nodes set to ensure deleted nodes are removed.
def cleanup_groups(groups):
    cleaned = {}
    for group_name, group_data in groups.items():
        valid_nodes = {
            nid: text 
            for nid, text in group_data.get("nodes", {}).items() 
            if nid != "None"
        }
        selected = group_data.get("selectedNodeId")
        if selected not in valid_nodes and valid_nodes:
            selected = next(iter(valid_nodes))
        cleaned[group_name] = {
            "originalName": group_data.get("originalName", group_name),
            "nodes": valid_nodes,
            "selectedNodeId": selected
        }
    return cleaned

class WriteTextPickMe:
    first_instance_ran = False  # Class-level variable
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "lines": 10}),
                "group": ("STRING", {"default": "default"})
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "save_text"
    CATEGORY = "Bjornulf"
    OUTPUT_NODE = True

    def save_text(self, text, group, unique_id):
        node_id = unique_id
        if not node_id:
            return (text,)

        with lock:
            if not WriteTextPickMe.first_instance_ran:
                empty_groups()
                remove_txt(group)
                WriteTextPickMe.first_instance_ran = True
            
            active_nodes.add(node_id)
            groups = load_groups()
            norm_group = normalize_group(group)

            group_data = groups.setdefault(norm_group, {
                "originalName": group,
                "nodes": {},
                "selectedNodeId": None
            })

            group_data["nodes"][node_id] = text
            group_data["selectedNodeId"] = node_id

            cleaned_groups = cleanup_groups(groups)
            save_groups(cleaned_groups)

        return (text,)

class PickMe:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "group": ("STRING", {"default": "default"}),
                "all_as_variables": ("BOOLEAN", {"default": False}),
                "include_red": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0x7FFFFFFFFFFFFFFF
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "LOG", "JSON", "FILE_CONTENT")
    FUNCTION = "select_text"
    CATEGORY = "Bjornulf"
    OUTPUT_NODE = True
    
    def select_text(self, group, all_as_variables, include_red, seed, prompt=None):
        current_writenodes = set()
        workflow_groups = {}
        
        if prompt is not None:
            for node_id, node_info in prompt.items():
                if node_info.get("class_type") == "WriteTextPickMe":
                    current_writenodes.add(node_id)
                    inputs = node_info.get("inputs", {})
                    group_name = inputs.get("group", "default")
                    text = inputs.get("text", "")
                    norm_group = normalize_group(group_name)
                    
                    if norm_group not in workflow_groups:
                        workflow_groups[norm_group] = {
                            "originalName": group_name,
                            "nodes": {},
                            "selectedNodeId": None
                        }
                    
                    workflow_groups[norm_group]["nodes"][node_id] = text
                    workflow_groups[norm_group]["selectedNodeId"] = node_id

        existing_groups = load_groups()
        merged_groups = workflow_groups.copy()
        
        # Preserve existing groups not in current workflow
        for gname, gdata in existing_groups.items():
            if gname not in merged_groups:
                merged_groups[gname] = gdata

        with lock:
            global active_nodes
            active_nodes.clear()
            active_nodes.update(current_writenodes)
            cleaned_groups = cleanup_groups(merged_groups)
            save_groups(cleaned_groups)

        norm_group = normalize_group(group)
        group_data = cleaned_groups.get(norm_group, {})
        text_output = ""
        
        if all_as_variables:
            variables = []
            for gname, gdata in cleaned_groups.items():
                name = gdata["originalName"]
                if include_red:
                    values = [v for v in gdata["nodes"].values() if v]
                    variables.append(f"{name} = {{{ '|'.join(values) }}}" if values else f"{name} = ")
                else:
                    selected = gdata["nodes"].get(gdata["selectedNodeId"], "")
                    variables.append(f"{name} = {selected}")
            text_output = "\n".join(variables)
        else:
            if include_red:
                text_output = "{" + "|".join(group_data.get("nodes", {}).values()) + "}"
            else:
                text_output = group_data.get("nodes", {}).get(group_data.get("selectedNodeId", ""), "")

        log_output = []
        for gname, gdata in cleaned_groups.items():
            log_output.append(f"Group: {gdata['originalName']} ({gname})")
            for nid, text in gdata['nodes'].items():
                log_output.append(f"  Node {nid}: {text}")
            log_output.append(f"  Selected: {gdata['selectedNodeId']}")
            log_output.append("")

        # Generate file content from current group data
        file_content = "\n".join([f"Node {nid}: {text}" for nid, text in group_data.get("nodes", {}).items()])

        # Write to text file
        file_dir = os.path.join("Bjornulf", "pickme")
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, f"{norm_group}.txt")
        try:
            with open(file_path, "w") as f:
                f.write(file_content)
        except Exception as e:
            print(f"Error writing to text file: {e}")

        return (
            text_output, 
            "\n".join(log_output).strip(),
            json.dumps(cleaned_groups, indent=2),
            file_content
        )

@PromptServer.instance.routes.post("/set_PickMe")
async def set_PickMe(request):
    try:
        data = await request.json()
        logging.info(f"data: {data}")
        group = normalize_group(data.get("group", ""))
        nodes = data.get("nodes", None)

        with lock:
            groups = load_groups()

            if nodes is not None:
                # Bulk update
                group_data = groups.setdefault(group, {
                    "originalName": data.get("originalName", group),
                    "nodes": {},
                    "selectedNodeId": None
                })

                group_data["nodes"].clear()
                for node in nodes:
                    node_id = str(node.get("id", ""))
                    text = node.get("text", "")
                    if node_id:
                        group_data["nodes"][node_id] = text

                # Update selection
                if group_data["nodes"]:
                    current_selected = group_data.get("selectedNodeId")
                    if current_selected not in group_data["nodes"]:
                        group_data["selectedNodeId"] = next(iter(group_data["nodes"].keys()))
                else:
                    group_data["selectedNodeId"] = None

                cleaned = cleanup_groups(groups)
                save_groups(cleaned)
                return web.json_response({"success": True})
            else:
                # Single node update
                node_id = str(data.get("nodeId", "")).strip()

                if not node_id.isdigit():
                    return web.json_response({"success": False, "error": "Invalid node ID"}, status=400)

                if data.get("isSelected"):
                    group_data = groups.setdefault(group, {
                        "originalName": data.get("group", group),
                        "nodes": {},
                        "selectedNodeId": None
                    })
                    group_data["nodes"][node_id] = data.get("text", "")
                    group_data["selectedNodeId"] = node_id
                else:
                    if group in groups:
                        if node_id in groups[group]["nodes"]:
                            del groups[group]["nodes"][node_id]
                        if groups[group]["selectedNodeId"] == node_id:
                            remaining_nodes = list(groups[group]["nodes"].keys())
                            groups[group]["selectedNodeId"] = remaining_nodes[0] if remaining_nodes else None

                cleaned = cleanup_groups(groups)
                save_groups(cleaned)

                group_data = cleaned.get(group, {
                    "originalName": group,
                    "nodes": {},
                    "selectedNodeId": None
                })
                selected_node_id = group_data.get("selectedNodeId")
                text = group_data["nodes"].get(selected_node_id, "")

                return web.json_response({
                    "success": True,
                    "selectedNodeId": selected_node_id,
                    "text": text
                })

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

@PromptServer.instance.routes.get("/get_PickMe")
async def get_PickMe(request):
    group_name = normalize_group(request.query.get("group", "default"))
    groups = load_groups()
    group_data = groups.get(group_name, {
        "originalName": group_name,
        "nodes": {},
        "selectedNodeId": None
    })
    
    return web.json_response({
        "originalName": group_data["originalName"],
        "nodeId": group_data["selectedNodeId"],
        "text": group_data["nodes"].get(group_data["selectedNodeId"], "")
    })