import torch
import torch.nn.functional as F

class SplitImageGrid:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rows": ("INT", {"default": 1, "min": 1, "max": 9}),
                "columns": ("INT", {"default": 1, "min": 1, "max": 9}),
                "MODIFIED_part_index": ("INT", {"default": 1, "min": 1, "max": 9}),
                "overlap_pixels": ("INT", {"default": 4, "min": 0, "max": 32}),
            }
        }

    RETURN_TYPES = ["IMAGE"] * 9 + ["INT", "INT", "IMAGE", "INT", "INT"]
    RETURN_NAMES = [f"part_{i}" for i in range(1, 10)] + ["rows", "columns", "MODIFIED_part", "MODIFIED_part_index", "overlap_pixels"]
    FUNCTION = "split"
    CATEGORY = "image"

    def split(self, image, rows, columns, MODIFIED_part_index, overlap_pixels):
        # Get image dimensions
        B, H, W, C = image.shape
        
        # Calculate exact part dimensions
        part_height = H // rows
        part_width = W // columns
        O = overlap_pixels
        
        # Store the exact coordinates for each part
        part_coordinates = []
        parts = []
        
        # Split image with overlap
        for r in range(rows):
            for c in range(columns):
                # Base coordinates without overlap
                base_h_start = r * part_height
                base_h_end = (r + 1) * part_height if r < rows - 1 else H
                base_w_start = c * part_width
                base_w_end = (c + 1) * part_width if c < columns - 1 else W
                
                # Add overlap, but respect image boundaries
                h_start = max(0, base_h_start - O)
                h_end = min(H, base_h_end + O)
                w_start = max(0, base_w_start - O)
                w_end = min(W, base_w_end + O)
                
                # Extract part and save coordinates
                part = image[:, h_start:h_end, w_start:w_end, :]
                parts.append(part)
                
                # Store exact coordinate info for precise reassembly
                part_coordinates.append({
                    'base_h_start': base_h_start,
                    'base_h_end': base_h_end,
                    'base_w_start': base_w_start,
                    'base_w_end': base_w_end,
                    'h_start': h_start,
                    'h_end': h_end,
                    'w_start': w_start,
                    'w_end': w_end
                })
        
        # Pad unused parts with None
        while len(parts) < 9:
            parts.append(None)
            part_coordinates.append(None)
        
        # Adjust MODIFIED_part_index to 0-based and validate
        MODIFIED_index = MODIFIED_part_index - 1
        if MODIFIED_index < 0 or MODIFIED_index >= rows * columns:
            raise ValueError(f"MODIFIED_part_index {MODIFIED_part_index} is out of range for {rows}x{columns} grid")
        MODIFIED_part = parts[MODIFIED_index]
        
        # Store part coordinates as metadata in tensor
        for i, part in enumerate(parts):
            if part is not None and part_coordinates[i] is not None:
                # Store as tensor attributes
                for key, value in part_coordinates[i].items():
                    setattr(part, f'_{key}', value)
        
        return tuple(parts + [rows, columns, MODIFIED_part, MODIFIED_part_index, overlap_pixels])

class ReassembleImageGrid:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "original": ("IMAGE",),
                "rows": ("INT", {"default": 1, "min": 1, "max": 10}),
                "columns": ("INT", {"default": 1, "min": 1, "max": 10}),
                "overlap_pixels": ("INT", {"default": 4, "min": 0, "max": 32}),
            },
            "optional": {
                "part_1": ("IMAGE",),
                "part_2": ("IMAGE",),
                "part_3": ("IMAGE",),
                "part_4": ("IMAGE",),
                "part_5": ("IMAGE",),
                "part_6": ("IMAGE",),
                "part_7": ("IMAGE",),
                "part_8": ("IMAGE",),
                "part_9": ("IMAGE",),
                "MODIFIED_part": ("IMAGE",),
                "MODIFIED_part_index": ("INT", {"default": 0, "min": 0, "max": 9}),
                "reference_video_part_index": ("INT", {"default": 0, "min": 0, "max": 9}),
                "auto_resize": ("BOOLEAN", {"default": True}),
                "use_feathering": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ["IMAGE"]
    RETURN_NAMES = ["image"]
    FUNCTION = "reassemble"
    CATEGORY = "image"

    def repeat_frames(self, tensor, k):
        """Repeat the tensor k times along the batch dimension."""
        return tensor.repeat(k, 1, 1, 1) if k > 1 else tensor

    def adjust_frame_count_with_repeat(self, tensor, B_ref, B_original):
        """Adjust frame count, considering repetition if B_ref ≈ k * B_original."""
        if B_original == 0:
            raise ValueError("Original frame count is zero")
        k = round(B_ref / B_original)
        if k > 0 and abs(B_ref - k * B_original) <= 1:
            repeated = self.repeat_frames(tensor, k)
            if repeated.shape[0] > B_ref:
                repeated = repeated[:B_ref]
            elif repeated.shape[0] < B_ref:
                pad_size = B_ref - repeated.shape[0]
                last_frame = repeated[-1:].repeat(pad_size, 1, 1, 1)
                repeated = torch.cat([repeated, last_frame], dim=0)
            return repeated
        else:
            return self.adjust_frame_count(tensor, B_ref)

    def adjust_frame_count(self, tensor, target_B):
        """Adjust the frame count of a tensor to match target_B."""
        B = tensor.shape[0]
        if B == target_B:
            return tensor
        indices = torch.linspace(0, B - 1, steps=target_B).round().long()
        indices = indices.clamp(0, B - 1)
        return tensor[indices]
    
    def resize_tensor(self, tensor, target_height, target_width):
        """Resize tensor to target dimensions using interpolation."""
        B, H, W, C = tensor.shape
        
        # Convert to proper format for F.interpolate
        tensor_BCHW = tensor.permute(0, 3, 1, 2)
        
        # Resize using bilinear interpolation
        resized = F.interpolate(
            tensor_BCHW, 
            size=(target_height, target_width), 
            mode='bilinear', 
            align_corners=False
        )
        
        # Convert back to original format
        return resized.permute(0, 2, 3, 1)

    def create_feather_mask(self, height, width, overlap, device):
        """Creates a feathering mask for blending overlapping regions."""
        # Create full size mask of ones
        mask = torch.ones((height, width), device=device)
        
        # Create linear gradients for edges
        if overlap > 0:
            # Linear ramp from 0 to 1
            ramp = torch.linspace(0, 1, overlap, device=device)
            
            # Apply feathering to edges
            mask[:overlap, :] = torch.min(mask[:overlap, :], ramp.view(-1, 1))
            mask[-overlap:, :] = torch.min(mask[-overlap:, :], torch.flip(ramp, [0]).view(-1, 1))
            mask[:, :overlap] = torch.min(mask[:, :overlap], ramp.view(1, -1))
            mask[:, -overlap:] = torch.min(mask[:, -overlap:], torch.flip(ramp, [0]).view(1, -1))
            
        return mask.unsqueeze(0).unsqueeze(-1)  # Add batch and channel dims

    def reassemble(self, original, rows, columns, overlap_pixels, 
                   part_1=None, part_2=None, part_3=None, part_4=None, part_5=None, 
                   part_6=None, part_7=None, part_8=None, part_9=None, 
                   MODIFIED_part=None, MODIFIED_part_index=0, 
                   reference_video_part_index=0, auto_resize=True, use_feathering=True):
        # Get original dimensions
        B, H, W, C = original.shape
        
        # Calculate part dimensions
        part_height = H // rows
        part_width = W // columns
        O = overlap_pixels
        parts = [part_1, part_2, part_3, part_4, part_5, part_6, part_7, part_8, part_9]

        # Override with MODIFIED_part if provided
        if MODIFIED_part is not None and MODIFIED_part_index > 0:
            index = MODIFIED_part_index - 1
            if index < 0 or index >= len(parts):
                raise ValueError(f"Invalid MODIFIED_part_index: {MODIFIED_part_index}")
            parts[index] = MODIFIED_part

        # Handle reference part for frame count
        if reference_video_part_index > 0:
            ref_index = reference_video_part_index - 1
            if parts[ref_index] is None:
                raise ValueError(f"Reference part {reference_video_part_index} is not provided")
            B_ref = parts[ref_index].shape[0]
            
            # Adjust frame counts for all parts
            original = self.adjust_frame_count_with_repeat(original, B_ref, B)
            for i in range(len(parts)):
                if parts[i] is not None and i != ref_index:
                    parts[i] = self.adjust_frame_count_with_repeat(parts[i], B_ref, parts[i].shape[0])
        else:
            B_ref = B

        # Create a fresh canvas for reassembly
        reassembled = original.clone()
        
        # If feathering is enabled, prepare data structures
        if use_feathering:
            accumulation = torch.zeros_like(reassembled)
            weight_accumulation = torch.zeros((B_ref, H, W, 1), device=original.device)

        # Reassemble parts
        for i, part in enumerate(parts):
            if part is not None:
                # Calculate grid position
                row = i // columns
                col = i % columns
                
                # Default positioning (fallback if metadata not available)
                h_start = row * part_height
                h_end = min(H, (row + 1) * part_height)
                w_start = col * part_width
                w_end = min(W, (col + 1) * part_width)
                
                # Read positioning metadata if available
                base_h_start = getattr(part, '_base_h_start', h_start)
                base_h_end = getattr(part, '_base_h_end', h_end)
                base_w_start = getattr(part, '_base_w_start', w_start)
                base_w_end = getattr(part, '_base_w_end', w_end)
                part_h_start = getattr(part, '_h_start', None)
                part_h_end = getattr(part, '_h_end', None)
                part_w_start = getattr(part, '_w_start', None)
                part_w_end = getattr(part, '_w_end', None)
                
                # Calculate offsets if we have full metadata
                if all(x is not None for x in [part_h_start, part_h_end, part_w_start, part_w_end]):
                    part_h_offset = base_h_start - part_h_start
                    part_w_offset = base_w_start - part_w_start
                    
                    # Extract the core part (without overlap)
                    core_h_start = part_h_offset if part_h_offset >= 0 else 0
                    core_h_end = part.shape[1] - (part_h_end - base_h_end) if part_h_end > base_h_end else part.shape[1]
                    core_w_start = part_w_offset if part_w_offset >= 0 else 0
                    core_w_end = part.shape[2] - (part_w_end - base_w_end) if part_w_end > base_w_end else part.shape[2]
                    
                    # Adjust to actual target position
                    target_h_start = base_h_start
                    target_h_end = base_h_end
                    target_w_start = base_w_start
                    target_w_end = base_w_end
                else:
                    # Simple extraction for parts without metadata
                    o_top = O if row > 0 else 0
                    o_bottom = O if row < rows - 1 else 0
                    o_left = O if col > 0 else 0
                    o_right = O if col < columns - 1 else 0
                    
                    core_h_start = o_top
                    core_h_end = part.shape[1] - o_bottom
                    core_w_start = o_left
                    core_w_end = part.shape[2] - o_right
                    
                    target_h_start = h_start
                    target_h_end = h_end
                    target_w_start = w_start
                    target_w_end = w_end
                
                # Extract the core part
                core_part = part[:, core_h_start:core_h_end, core_w_start:core_w_end, :]
                
                # Resize if necessary
                target_h_size = target_h_end - target_h_start
                target_w_size = target_w_end - target_w_start
                if auto_resize and (core_part.shape[1] != target_h_size or core_part.shape[2] != target_w_size):
                    core_part = self.resize_tensor(core_part, target_h_size, target_w_size)
                
                # Ensure correct frame count
                if core_part.shape[0] != B_ref:
                    core_part = self.adjust_frame_count(core_part, B_ref)
                
                # Place the part in the final image
                if use_feathering:
                    # Create feathering mask
                    mask = self.create_feather_mask(
                        core_part.shape[1], 
                        core_part.shape[2],
                        min(O, core_part.shape[1]//4, core_part.shape[2]//4),  # Limit feathering to 1/4 of part size
                        core_part.device
                    ).expand(B_ref, -1, -1, C)
                    
                    # Multiply by the mask
                    weighted_part = core_part * mask
                    
                    # Add to accumulation
                    accumulation[:, target_h_start:target_h_end, target_w_start:target_w_end, :] += weighted_part
                    weight_accumulation[:, target_h_start:target_h_end, target_w_start:target_w_end, :] += mask[:, :, :, :1]
                else:
                    # Direct assignment
                    reassembled[:, target_h_start:target_h_end, target_w_start:target_w_end, :] = core_part
        
        # Final normalization if feathering is used
        if use_feathering:
            # Prevent division by zero
            weight_accumulation = torch.clamp(weight_accumulation, min=1e-5)
            # Normalize
            reassembled = accumulation / weight_accumulation
        
        return (reassembled,)