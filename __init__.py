import os
import importlib
import sys

from .show_stuff import ShowFloat, ShowInt, ShowStringText, ShowJson
from .write_text import WriteText, WriteTextAppend
from .text_replace import TextReplace, TextGrep
from .combine_texts import CombineTexts
from .loop_texts import LoopTexts
from .random_texts import RandomTexts
from .loop_float import LoopFloat
from .loop_integer import LoopInteger
from .loop_basic_batch import LoopBasicBatch
from .show_text import ShowText
from .save_text import SaveText
from .save_tmp_image import SaveTmpImage, LoadTmpImage
from .save_img_to_folder import SaveImageToFolder, SaveImageWithTextToFolder
from .resize_image_percentage import ResizeImagePercentage
from .remove_transparency import RemoveTransparency
from .image_to_grayscale import GrayscaleTransform
from .random_line_from_input import RandomLineFromInput
from .loop_lines import LoopAllLines
from .random_seed_with_text import TextToStringAndSeed
from .load_image_alpha import LoadImageWithTransparency
from .image_mask_cutter import ImageMaskCutter
from .loop_combine_texts_by_lines import CombineTextsByLines
from .loop_images import LoopImages
from .random_image import RandomImage
from .write_text_advanced import WriteTextAdvanced
from .loop_write_text import LoopWriteText
from .load_images_from_folder import LoadImagesFromSelectedFolder
from .select_image_from_list import SelectImageFromList
from .if_else import IfElse, MatchTextToInput, MatchTextToInput30
from .image_details import ImageDetails
from .combine_images import CombineImages
from .loop_lines_sequential import LoopLinesSequential
from .images_merger_horizontal import MergeImagesHorizontally, MergeBatchImagesHorizontal
from .images_merger_vertical import MergeImagesVertically
from .text_to_anything import TextToAnything
from .anything_to_text import AnythingToText
from .anything_to_int import AnythingToInt
from .anything_to_float import AnythingToFloat
from .string_splitter import TextSplitin5, TextSplitin10
from .line_selector import LineSelector
from .note_text import DisplayNote
from .global_variables import LoadGlobalVariables, SaveGlobalVariables
from .write_pickme_chain import WriteTextPickMeChain
from .text_to_variable import TextToVariable
from .random_stuff import RandomIntNode, RandomFloatNode
from .global_seed_manager import GlobalSeedManager
from .switches import SwitchText, SwitchAnything
from .write_pickme_global import WriteTextPickMeGlobal, LoadTextPickMeGlobal
from .list_selector import ListSelector
from .math_node import MathNode
from .save_tmp_video import SaveTmpVideo
from .split_image import SplitImageGrid, ReassembleImageGrid
from .loop_random_seed import LoopRandomSeed
from .image_cut_and_shift import HorizontalCutAndShift
from .load_image_from_path import LoadImageWithTransparencyFromPath
from .upscaler_transparency import ImageUpscaleWithModelTransparency
from .load_base64_transparency import loadImageBase64Transparency
from .pickme_image import WriteImagePickMeGlobal, LoadImagePickMeGlobal, WriteImagePickMeGlobalInput
from .pickme_image_video_prompt import WriteImageVideoPromptPickMeGlobal, LoadImageVideoPromptPickMeGlobal
from .save_video_to_folder import SaveVideoToFolder
from .save_tmp_text import SaveTmpText, LoadTmpText
from .audio_add_silence import AddSilenceToAudio, PadAudioToDuration
from .save_video_ffv1 import SaveVideoFFV1
from .save_video_as_images import SaveVideoAsImages
from .base64_videos import VideoToBase64, Base64ToVideo
from .pickme_character_lora import WriteCharacterPickMeGlobal, LoadCharacterPickMeGlobal
from .send_null_same_as_disconnected import ConditionalNull
from .wait import WaitingNode
from .audio_fix_2_channels import AudioChannelFixer

NODE_CLASS_MAPPINGS = {
    "Bjornulf_AudioChannelFixer": AudioChannelFixer,
    "Bjornulf_WaitingNode": WaitingNode,
    "Bjornulf_ConditionalNull": ConditionalNull,
    "Bjornulf_WriteCharacterPickMeGlobal": WriteCharacterPickMeGlobal,
    "Bjornulf_LoadCharacterPickMeGlobal": LoadCharacterPickMeGlobal,
    "Bjornulf_VideoToBase64": VideoToBase64,
    "Bjornulf_Base64ToVideo": Base64ToVideo,
    "Bjornulf_SaveVideoFFV1": SaveVideoFFV1,
    "Bjornulf_SaveVideoAsImages": SaveVideoAsImages,
    "Bjornulf_AddSilenceToAudio": AddSilenceToAudio,
    "Bjornulf_PadAudioToDuration": PadAudioToDuration,
    "Bjornulf_WriteImageVideoPromptPickMeGlobal": WriteImageVideoPromptPickMeGlobal,
    "Bjornulf_LoadImageVideoPromptPickMeGlobal": LoadImageVideoPromptPickMeGlobal,
    "Bjornulf_SaveTmpText": SaveTmpText,
    "Bjornulf_LoadTmpText": LoadTmpText,
    "Bjornulf_SaveVideoToFolder": SaveVideoToFolder,
    "Bjornulf_WriteImagePickMeGlobal": WriteImagePickMeGlobal,
    "Bjornulf_WriteImagePickMeGlobalInput": WriteImagePickMeGlobalInput,
    "Bjornulf_LoadImagePickMeGlobal": LoadImagePickMeGlobal,
    "Bjornulf_TextGrep": TextGrep,
    "Bjornulf_ImageUpscaleWithModelTransparency": ImageUpscaleWithModelTransparency,
    "Bjornulf_loadImageBase64Transparency": loadImageBase64Transparency,
    "Bjornulf_MatchTextToInput": MatchTextToInput,
    "Bjornulf_MatchTextToInput30": MatchTextToInput30,
    "Bjornulf_LoopRandomSeed": LoopRandomSeed,
    "Bjornulf_HorizontalCutAndShift": HorizontalCutAndShift,
    "Bjornulf_LoadImageWithTransparencyFromPath": LoadImageWithTransparencyFromPath,
    "Bjornulf_SplitImageGrid": SplitImageGrid,
    "Bjornulf_ReassembleImageGrid": ReassembleImageGrid,
    "Bjornulf_SaveTmpAudio": SaveTmpAudio,
    "Bjornulf_SaveTmpVideo": SaveTmpVideo,
    "Bjornulf_MathNode": MathNode,
    "Bjornulf_ListSelector": ListSelector,
    "Bjornulf_WriteTextPickMeGlobal": WriteTextPickMeGlobal,
    "Bjornulf_LoadTextPickMeGlobal": LoadTextPickMeGlobal,
    "Bjornulf_SwitchText": SwitchText,
    "Bjornulf_SwitchAnything": SwitchAnything,
    "Bjornulf_GlobalSeedManager": GlobalSeedManager,
    "Bjornulf_RandomIntNode": RandomIntNode,
    "Bjornulf_RandomFloatNode": RandomFloatNode,
    "Bjornulf_TextToVariable": TextToVariable,
    "Bjornulf_WriteTextPickMeChain": WriteTextPickMeChain,
    "Bjornulf_LoadGlobalVariables": LoadGlobalVariables,
    "Bjornulf_SaveGlobalVariables": SaveGlobalVariables,
    "Bjornulf_DisplayNote": DisplayNote,
    "Bjornulf_LineSelector": LineSelector,
    "Bjornulf_TextSplitin5": TextSplitin5,
    "Bjornulf_TextSplitin10": TextSplitin10,
    "Bjornulf_ShowInt": ShowInt, 
    "Bjornulf_TextReplace" : TextReplace,
    "Bjornulf_ShowFloat": ShowFloat,
    "Bjornulf_ShowJson": ShowJson,
    "Bjornulf_ShowStringText": ShowStringText,
    "Bjornulf_TextToAnything": TextToAnything,
    "Bjornulf_AnythingToText": AnythingToText,
    "Bjornulf_AnythingToInt": AnythingToInt,
    "Bjornulf_AnythingToFloat": AnythingToFloat,
    "Bjornulf_MergeImagesHorizontally": MergeImagesHorizontally,
    "Bjornulf_MergeBatchImagesHorizontal": MergeBatchImagesHorizontal,
    "Bjornulf_MergeImagesVertically": MergeImagesVertically,
    "Bjornulf_LoopLinesSequential": LoopLinesSequential,
    "Bjornulf_CombineImages": CombineImages,
    "Bjornulf_ImageDetails": ImageDetails,
    "Bjornulf_IfElse": IfElse,
    "Bjornulf_SelectImageFromList": SelectImageFromList,
    "Bjornulf_WriteText": WriteText,
    "Bjornulf_WriteTextAppend": WriteTextAppend,
    "Bjornulf_LoadImagesFromSelectedFolder": LoadImagesFromSelectedFolder,
    "Bjornulf_LoopWriteText": LoopWriteText,
    "Bjornulf_LoopImages": LoopImages,
    "Bjornulf_RandomImage": RandomImage,
    "Bjornulf_CombineTextsByLines": CombineTextsByLines,
    "Bjornulf_ImageMaskCutter": ImageMaskCutter,
    "Bjornulf_LoadImageWithTransparency": LoadImageWithTransparency,
    "Bjornulf_LoopAllLines": LoopAllLines,
    "Bjornulf_TextToStringAndSeed": TextToStringAndSeed,
    "Bjornulf_RandomLineFromInput": RandomLineFromInput,
    "Bjornulf_WriteTextAdvanced": WriteTextAdvanced,
    "Bjornulf_RemoveTransparency": RemoveTransparency,
    "Bjornulf_GrayscaleTransform": GrayscaleTransform,
    "Bjornulf_ShowText": ShowText,
    "Bjornulf_SaveText": SaveText,
    "Bjornulf_ResizeImagePercentage": ResizeImagePercentage,
    "Bjornulf_SaveImageToFolder": SaveImageToFolder,
    "Bjornulf_SaveImageWithTextToFolder": SaveImageWithTextToFolder,
    "Bjornulf_SaveTmpImage": SaveTmpImage,
    "Bjornulf_LoadTmpImage": LoadTmpImage,
    "Bjornulf_CombineTexts": CombineTexts,
    "Bjornulf_LoopTexts": LoopTexts,
    "Bjornulf_RandomTexts": RandomTexts,
    "Bjornulf_LoopFloat": LoopFloat,
    "Bjornulf_LoopInteger": LoopInteger,
    "Bjornulf_LoopBasicBatch": LoopBasicBatch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Bjornulf_AudioChannelFixer": "🎵🔧 Audio 2 Channels Fixer",
    "Bjornulf_ApplySpeechBubbleYOLO": "🗨️ Apply Speech Bubble YOLO",

    "Bjornulf_WaitingNode": "⏳ Waiting Node",
    "Bjornulf_CharacterCreator": "👤💾 Character Creator",
    "Bjornulf_CharacterLoader": "👤📥 Character Loader",
    "Bjornulf_RunOnRunpod": "☁️ Runpod - Run On Runpod",
    "Bjornulf_RunLoraTrainingRunpodZImageTurbo": "☁️ Runpod - 🏋️‍♂️ Train Lora ZImageTurbo",
    "Bjornulf_ExecuteWorkflowT2VinstaGirlsRUNPOD": "☁️ Runpod - 🔮✒➜📹 InstaGirls T2V use v2",
    "Bjornulf_ImageGeneratorGrok": "🌐✒➜🖼 Image Generator Grok (Browser injection)",
    "Bjornulf_VideoGeneratorGrok": "🌐✒➜📹 Video Generator Grok (Browser injection)",
    "Bjornulf_TextGeneratorGrok": "🌐✒➜✒ Text Generator Grok (Browser injection)",
    "Bjornulf_ImageDescriptionGrok": "🌐🖼➜📝 Image Description Grok (Browser injection)",
    "Bjornulf_ImageGeneratorSeaArt": "🌐✒➜🖼 Image Generator SeaArt (Browser injection)",
    "Bjornulf_ImageGeneratorHiggsfield": "🌐✒➜🖼 Image Generator Higgsfield (Browser injection)",
    "Bjornulf_ImageGeneratorHiggsfieldMultiprompt": "🌐✒➜🖼 Image Generator Higgsfield Multiprompt (Browser injection)",
    "Bjornulf_ImageGeneratorHiggsfieldMultipromptList": "🌐✒➜🖼 Image Generator Higgsfield Multiprompt List (Browser injection)",
    "Bjornulf_ImageToVideoGeneratorGrokFirstRun": "🌐🖼➜📹 Image to Video Generator Grok (First Run)",
    "Bjornulf_ImageToVideoGeneratorGrokSecondRun": "🌐🖼➜📹 Image to Video Generator Grok (Second Run, current image from first run)",

    "Bjornulf_ConditionalNull": "🚫 Send Null (Same as Disconnected)",
    "Bjornulf_ExecuteWorkflowIP2Iv2": "🔮🖼👺➜🖼️ Image IP2I / IP2V use v2 (Wan Animate)",
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": "🖼️💾 Save PNG ZIP and Preview RGBA Animated WEBP",
    "Bjornulf_ExecuteWorkflowI2Mv2": "🔮🖼➜🖼👺 Image I2M use v2",
    "Bjornulf_WriteCharacterPickMeGlobal": "🌎✒🖼👉 Write Character Prompt (Global Pick Me)",
    "Bjornulf_LoadCharacterPickMeGlobal": "🌎📥🖼 Load Character Prompt (Global Pick Me)",
    "Bjornulf_ExecuteWorkflowV2Vv2": "🔮 📹➜📹 Video V2V use v2",
    "Bjornulf_ExecuteWorkflowIVV2Vv2": "🔮 🖼📹📹➜📹 Video IVV2V use v2",
    "Bjornulf_DWPoseFaceScaleCalculator": "🤖🎭 DWPose Face Scale Calculator",
    "Bjornulf_ExecuteWorkflowIV2V": "🔮🖼➜📹 Video IV2V use v2",
    "Bjornulf_RunLoraTrainingRunpodWAN22": "☁️ Runpod - 🏋️‍♂️ Train Lora WAN22",
    "Bjornulf_TrainLoraWAN22Runpod": "☁️ Runpod - 🏋️‍♂️ Train Lora WAN22 (claude)",
    "Bjornulf_VideoToBase64": "📹➜🔤 Video to Base64",
    "Bjornulf_Base64ToVideo": "🔤➜📹 Base64 to Video",
    "Bjornulf_ExecuteWorkflowI2IHiresPainting": "🌿 Yaturu - 🔮🖼➜🖼 Upscale x2 Painting",
    "Bjornulf_ExecuteWorkflowI2IHiresPhotography": "🌿 Yaturu - 🔮🖼➜🖼 Upscale x2 Photography",
    "Bjornulf_ExecuteWorkflowIT2ITransformPhotography": "🌿 Yaturu - 🔮🖼➜🖼 Painting to Photography",
    "Bjornulf_ExecuteWorkflowT2ATts": "🌿 Yaturu - 🔮✒➜🔊 Text to Speech",
    "Bjornulf_ExecuteWorkflowIA2VAMakeCharacterTalk": "🌿 Yaturu - 🔮🖼🔊➜📹🔊 Video : Make Character Talk",
    "Bjornulf_ExecuteWorkflowFLF2VPainting2Real": "🌿 Yaturu - 🔮🖼🖼➜📹 Video : Transition Painting to Real",
    "Bjornulf_ZoomToAreaVideoYaturu": "🌿 Yaturu - 📹🔍 Zoom To Area",
    "Bjornulf_FalLipSyncNode": "🌿 Yaturu - 🔮👄📹🔊 FalAI Lip Sync Node",
    "Bjornulf_FalNanoBananaClothingSwap": "🌿 Yaturu - 🔮👕👗 FalAI Nano Banana Clothing Swap",
    "Bjornulf_FalNanoBananaEdit": "🌿 Yaturu - 🔮✂️ FalAI Nano Banana Edit",
    "Bjornulf_FalSeedreamEdit": "🌿 Yaturu - 🔮✂️ FalAI Seedream Edit",
    "Bjornulf_ExecuteWorkflowRunpodStorageLessWAN22": "☁️ Runpod - 🔮 Execute Workflow StorageLess WAN22 (use v2)",
    "Bjornulf_SaveVideoFFV1": "💾📹 FFV1 Lossless Video Save",
    "Bjornulf_SaveVideoAsImages": "💾🖼️ Save Video as PNG Frames",
    "Bjornulf_AddSilenceToAudio": "🔊 Add silence to audio",
    "Bjornulf_PadAudioToDuration": "🔊 Pad audio to duration (Add silence)",
    "Bjornulf_AudioConcatenateSave": "🔊➕💾 Audio Concatenate and Save",
    "Bjornulf_WriteImageVideoPromptPickMeGlobal": "🌎✒🖼📹👉 Write Image + Video Prompt (Global Pick Me)",
    "Bjornulf_LoadImageVideoPromptPickMeGlobal": "🌎📥🖼📹 Load Image + Video Prompt (Global Pick Me)",
    "Bjornulf_LoadPickAudioFile": "📥🎵 Load Pick Audio File",
    "Bjornulf_FaceCropVideoNode": "🎭🔪 Face Crop Video Node",
    "Bjornulf_FaceCompositeVideoNode": "🎭🔧 Face Composite Video Node",
    "Bjornulf_AudioFrameCalculator": "🔢 Audio Frame Calculator",
    "Bjornulf_BasketImageHolder": "🖼 Image Holder 🧺 Basket",
    "Bjornulf_BasketMultipleAudioHolder": "🎵 Audio Holder 🧺 Basket 🤏 Grab",
    "Bjornulf_BasketMultipleImagesHolder": "🖼 Images Holder 🧺 Basket 🤏 Grab",
    "Bjornulf_BasketTextHolder": "📝 Load Text Holder 🧺 Basket",
    "Bjornulf_BasketMultipleVideosHolder": "📹 Video Holder 🧺 Basket",
    "Bjornulf_SaveTmpText": "💾 Save Temporary Text (tmp_api.txt) ⚠️💣",
    "Bjornulf_LoadTmpText": "📥 Load Temporary Text (tmp_api.txt) ⚠️💣",
    "Bjornulf_GrokAPINode": "🤖📝 Grok Text Generator",
    "Bjornulf_LLMPromptList": "📝 LLM Prompt List",
    "Bjornulf_SaveVideoToFolder": "💾📹📁 Save Video to Folder",
    "Bjornulf_ExtractSharpFramesFromVideoEnd": "🔍 Extract Sharp Frames from Video",
    "Bjornulf_VideoBlurrinessTextNode": "🔍 Video Blurriness Text Node",
    "Bjornulf_VisionCheckConfig": "🔮🦙👁♻ Vision Check Config",
    "Bjornulf_ExecuteWorkflowSDXL": "🔮 Execute Workflow - SDXL only",
    "Bjornulf_ExecuteWorkflowI2V": "🔮 Execute Workflow 🖼➜📹 : i2v",
    "Bjornulf_ExecuteWorkflowT2V": "🔮 Execute Workflow ✒➜📹 : t2v",
    "Bjornulf_ExecuteWorkflowI2I": "🔮 Execute Workflow 🖼➜🖼 : i2i",
    "Bjornulf_ExecuteWorkflowIIT2I": "🔮 Execute Workflow 🖼🖼✒➜🖼 : iit2i",
    "Bjornulf_ExecuteWorkflowIT2I": "🔮 Execute Workflow 🖼✒➜🖼 : it2i",
    "Bjornulf_ExecuteWorkflowT2I": "🔮 Execute Workflow ✒➜🖼 : t2i",
    "Bjornulf_ExecuteWorkflowIC2I": "🔮 Execute Workflow 🖼📥➜🖼 : ic2i (checkpoint/model)",
    "Bjornulf_ExecuteWorkflowIM2I": "🔮 Execute Workflow 🖼👺➜🖼 : im2i (mask)",
    "Bjornulf_ExecuteWorkflowI2M": "🔮 Execute Workflow 🖼➜👺 : i2m (mask)",
    "Bjornulf_ExecuteWorkflowFLF2V": "🔮 Execute Workflow 🖼🖼➜📹 : flf2V (Last frame)",
    "Bjornulf_ExecuteWorkflowVA2VA": "🔮 Execute Workflow 📹🔊➜📹🔊 : va2va (Video/audio)",
    "Bjornulf_ExecuteWorkflowT2A": "🔮 Execute Workflow ✒➜🔊 : t2a (Text to Audio)",
    "Bjornulf_ExecuteWorkflowIA2VA": "🔮 Execute Workflow 🖼🔊➜📹🔊 : ia2va (Image/Audio to Video/Audio)",
    "Bjornulf_ExecuteWorkflowV2V": "🔮 Execute Workflow 📹➜📹 : v2v (Video to Video)",
    "Bjornulf_ExecuteWorkflowT2VinstaGirls": "🔮 Execute Workflow ✒➜📹 : t2v/t2i instaGirls (+ char lora) use v2",
    "Bjornulf_ExecuteWorkflowIIIT2I": "🔮 Execute Workflow 🖼🖼🖼✒➜🖼 : iiit2i use v2 (Qwen Image Edit)",
    "Bjornulf_ConfigExecuteWorkflow": "🔮⚙ Config Execute Workflow",
    "Bjornulf_CheckpointLoaderPath": "📥 Load Checkpoint (with Path)",
    "Bjornulf_WriteImagePickMeGlobal": "🌎✒🖼👉 Write Image (Global Pick Me)",
    "Bjornulf_WriteImagePickMeGlobalInput": "🌎✒🖼👉 Write Image Input (Global Pick Me)",
    "Bjornulf_LoadImagePickMeGlobal": "🌎📥🖼 Load Image (Global Pick Me)",
    "Bjornulf_ExecuteWorkflowRunpodCreateWant2v": "🔮 Runpod Wan t2v",
    "Bjornulf_ExecuteWorkflowRunpodCreateWani2v": "🔮 Runpod Wan i2v (use v2)",
    "Bjornulf_DeleteRunpodPod": "🗑️ Delete Runpod Pod",
    "Bjornulf_DeepSeek": "🤖📝 DeepSeek Text Generator",
    "Bjornulf_ExecuteWorkflowSimplified": "🔮 Execute Workflow (Simplified)",
    "Bjornulf_ExecuteWorkflow_i2v_fusion": "🔮 Execute Workflow 🖼➜📹 : i2v Fusion 576p 81 frames",
    "Bjornulf_TextGrep": "🔍 Find text (Grep)",
    "Bjornulf_ImageResizer": "🖼 Resize Image (240p to 4k)",
    "Bjornulf_ImageResizerAdvanced": "🖼 Resize Image Advanced (240p to 4k) + ratio Crop / Pad",
    "Bjornulf_ImageResizerToReference": "🖼 Resize Image to Reference Image (with Crop / Pad)",
    "Bjornulf_loadImageBase64Transparency": "📥🖼 Load Image Base64 (Transparency)",
    "Bjornulf_ImageUpscaleWithModelTransparency": "🖼 Upscale Image with Transparency (with model)",
    "Bjornulf_JSONImagePromptExtractor": "JSONImagePromptExtractor", 
    "Bjornulf_MatchTextToInput": "🔛📝 Match 10 Text to Input",
    "Bjornulf_MatchTextToInput30": "🔛📝 Match 30 Text to Input",
    "Bjornulf_OpenAIVisionNode": "🔮 OpenAI Vision Node",
    "Bjornulf_OpenAIVisionNode10Images": "🔮 OpenAI Vision Node (10 images)",
    "Bjornulf_HandDetector": "🖐️ Hand Detector",
    "Bjornulf_HandDetectorRecombine": "🖐️ Hand Detector (Recombine)",
    "Bjornulf_LoopRandomSeed": "♻🎲 Loop Random Seed",
    "Bjornulf_LoadImageWithTransparencyFromPath": "📥🖼 Load Image with Transparency From Path",
    "Bjornulf_HorizontalCutAndShift": "🔪🖼 Horizontal Cut and Shift 🔼🔽",
    "Bjornulf_FixFace": "[BETA] 🔧🧑 Fix Face",
    "Bjornulf_FaceSettings": "[BETA] 🧑 Face Settings [Fix Face] ⚙",
    "Bjornulf_ApiDynamicTextInputs": "[BETA] 📥🔮📝 Text Manager Api (Execute Workflow)",
    "Bjornulf_ExecuteWorkflowNode": "[BETA] 🔮⚡ Remote Execute Workflow",
    "Bjornulf_LoadCivitAILinks": "📥🕑🤖 Load CivitAI Links",
    "Bjornulf_ReassembleImageGrid": "🖼📹🔨 Reassemble Image/Video Grid",
    "Bjornulf_SplitImageGrid": "🖼📹🔪 Split Image/Video Grid",
    "Bjornulf_SaveTmpAudio": "💾🔊 Save Audio (tmp_api.wav/mp3) ⚠️💣",
    "Bjornulf_SaveTmpVideo": "💾📹 Save Video (tmp_api.mp4/mkv/webm) ⚠️💣",
    "Bjornulf_AudioPreview": "🔊▶ Audio Preview (Audio player)",
    "Bjornulf_MathNode": "🧮 Basic Math",
    "Bjornulf_TextAnalyzer": "📊🔍 Text Analyzer",
    "Bjornulf_OllamaVisionPromptSelector": "🦙👁 Ollama Vision Prompt Selector",
    "Bjornulf_WriteTextAppend": "📝➕ Write Text Append",
    "Bjornulf_ListSelector": "📑👈 Select from List",
    "Bjornulf_PlayAudio": "🔊▶ Play Audio",
    "Bjornulf_SwitchText": "🔛📝 Text Switch On/Off",
    "Bjornulf_SwitchAnything": "🔛✨ Anything Switch On/Off",
    "Bjornulf_GlobalSeedManager": "🌎🎲 Global Seed Manager",
    "Bjornulf_RandomIntNode": "🎲 Random Integer",
    "Bjornulf_RandomFloatNode": "🎲 Random Float",
    "Bjornulf_WriteTextPickMeGlobal": "🌎✒👉 Global Write Pick Me",
    "Bjornulf_LoadTextPickMeGlobal": "🌎📥 Load Global Pick Me",
    "Bjornulf_TextToVariable": "📌🅰️ Set Variable from Text",
    "Bjornulf_WriteTextPickMeChain": "✒👉 Write Pick Me Chain",
    "Bjornulf_FourImageViewer": "🖼👁 Preview 1-4 images (compare)",
    "Bjornulf_PreviewFirstImage": "🖼👁 Preview (first) image",
    "Bjornulf_AllLoraSelector": "👑 Combine Loras, Lora stack",
    "Bjornulf_LoadGlobalVariables": "📥🅰️ Load Global Variables",
    "Bjornulf_SaveGlobalVariables": "💾🅰️ Save Global Variables",
    "Bjornulf_DisplayNote": "📒 Note",
    "Bjornulf_KokoroTTS": "📝➜🔊 Kokoro - Text to Speech",
    "Bjornulf_LineSelector": "📝👈🅰️ Line selector (🎲 or ♻ or ♻📑)",
    "Bjornulf_LoaderLoraWithPath": "📥👑 Load Lora with Path",
    "Bjornulf_TextSplitin5": "📝🔪 Text split in 5",
    "Bjornulf_TextSplitin10": "📝🔪 Text split in 10",
    "Bjornulf_LatentResolutionSelector": "🩷 Empty Latent Selector",
    "Bjornulf_CivitAIModelSelectorSD15": "📥 Load checkpoint SD1.5 (+Download from CivitAi)",
    "Bjornulf_CivitAIModelSelectorSDXL": "📥 Load checkpoint SDXL (+Download from CivitAi)",
    "Bjornulf_CivitAIModelSelectorPony": "📥 Load checkpoint Pony (+Download from CivitAi)",
    "Bjornulf_CivitAIModelSelectorFLUX_D": "📥 Load checkpoint FLUX Dev (+Download from CivitAi)",
    "Bjornulf_CivitAIModelSelectorFLUX_S": "📥 Load checkpoint FLUX Schnell (+Download from CivitAi)",
    "Bjornulf_CivitAILoraSelectorSD15": "📥👑 Load Lora SD1.5 (+Download from CivitAi)",
    "Bjornulf_CivitAILoraSelectorSDXL": "📥👑 Load Lora SDXL (+Download from CivitAi)",
    "Bjornulf_CivitAILoraSelectorPONY": "📥👑 Load Lora Pony (+Download from CivitAi)",
    "Bjornulf_CivitAILoraSelectorHunyuan": "📥👑📹 Load Lora Hunyuan Video (+Download from CivitAi)",
    "Bjornulf_APIGenerateFalAI": "☁🎨 API Image Generator (FalAI) 🎨☁",
    "Bjornulf_APIGenerateCivitAI": "☁🎨 API Image Generator (CivitAI) 🎨☁",
    "Bjornulf_APIGenerateCivitAIAddLORA": "☁👑 Add Lora (API ONLY - CivitAI) 👑☁",
    "Bjornulf_ListLooperPose": "♻💃🕺📝 List Looper (Text Generator Poses)",
    "Bjornulf_ShowInt": "👁 Show (Int)",
    "Bjornulf_ShowFloat": "👁 Show (Float)",
    "Bjornulf_ShowJson": "👁 Show (JSON)",
    "Bjornulf_ShowStringText": "👁 Show (String/Text)",
    "Bjornulf_OllamaTalk": "🦙💬 Ollama Talk",
    "Bjornulf_OllamaImageVision": "🦙👁 Ollama Vision",
    "Bjornulf_TextToAnything": "📝➜✨ Text to Anything",
    "Bjornulf_AnythingToText": "✨➜📝 Anything to Text",
    "Bjornulf_AnythingToInt": "✨➜🔢 Anything to Int",
    "Bjornulf_AnythingToFloat": "✨➜🔢 Anything to Float",
    "Bjornulf_TextReplace": "📝➜📝 Replace text (Sed)",
    "Bjornulf_AddLineNumbers": "🔢 Add line numbers",
    "Bjornulf_FFmpegConfig": "⚙📹 FFmpeg Configuration 📹⚙",
    "Bjornulf_ConvertVideo": "📹➜📹 Convert Video (FFmpeg)",
    "Bjornulf_VideoDetails": "📹🔍 Video details (FFmpeg) ⚙",
    "Bjornulf_WriteText": "✒ Write Text",
    "Bjornulf_MergeImagesHorizontally": "🖼🖼 Merge Images/Videos 📹📹 (Horizontally)",
    "Bjornulf_MergeBatchImagesHorizontal": "🖼🖼 Merge Images/Videos 📹📹 (Horizontally - BATCH)",
    "Bjornulf_MergeImagesVertically": "🖼🖼 Merge Images/Videos 📹📹 (Vertically)",
    "Bjornulf_ConcatVideos": "📹🔗 Concat Videos (FFmpeg)",
    "Bjornulf_ConcatVideosFromList": "📹🔗 Concat Videos from list (FFmpeg)",
    "Bjornulf_LoopLinesSequential": "♻📑 Loop Sequential (input Lines)",
    "Bjornulf_LoopIntegerSequential": "♻📑 Loop Sequential (Integer)",
    "Bjornulf_LoopLoraSelector": "♻👑 Loop Lora Selector",
    "Bjornulf_RandomLoraSelector": "🎲👑 Random Lora Selector",
    "Bjornulf_LoopModelSelector": "♻ Loop Load checkpoint (Model Selector)",
    "Bjornulf_VideoPreview": "📹👁 Video Preview",
    "Bjornulf_ImagesListToVideo": "🖼➜📹 Images to Video path (tmp video) (FFmpeg)",
    "Bjornulf_VideoToImagesList": "📹➜🖼 Video Path to Images (Load video)",
    "Bjornulf_AudioVideoSync": "🔊📹 Audio Video Sync",
    "Bjornulf_WriteTextAdvanced": "✒🗔🅰️ Advanced Write Text",
    "Bjornulf_LoopWriteText": "♻ Loop (✒🗔🅰️ Advanced Write Text)",
    "Bjornulf_LoopModelClipVae": "♻ Loop (Model+Clip+Vae)",
    "Bjornulf_LoopImages": "♻🖼 Loop (Images)",
    "Bjornulf_CombineTextsByLines": "♻ Loop (All Lines from input 🔗 combine by lines)",
    "Bjornulf_LoopTexts": "♻ Loop (Texts)",
    "Bjornulf_LoopFloat": "♻ Loop (Float)",
    "Bjornulf_LoopInteger": "♻ Loop (Integer)",
    "Bjornulf_LoopBasicBatch": "♻ Loop",
    "Bjornulf_LoopAllLines": "♻ Loop (All Lines from input)",
    "Bjornulf_LoopSamplers": "♻ Loop (All Samplers)",
    "Bjornulf_LoopSchedulers": "♻ Loop (All Schedulers)",
    "Bjornulf_LoopCombosSamplersSchedulers": "♻ Loop (My combos Sampler⚔Scheduler)",
    "Bjornulf_RandomImage": "🎲🖼 Random Image",
    "Bjornulf_RandomLineFromInput": "🎲 Random line from input",
    "Bjornulf_RandomTexts": "🎲 Random (Texts)",
    "Bjornulf_RandomModelClipVae": "🎲 Random (Model+Clip+Vae)",
    "Bjornulf_RandomModelSelector": "🎲 Random Load checkpoint (Model Selector)",
    "Bjornulf_CharacterDescriptionGenerator": "🧑📝 Character Description Generator",
    "Bjornulf_GreenScreenToTransparency": "🟩➜▢ Green Screen to Transparency",
    "Bjornulf_TextToStringAndSeed": "🔢🎲 Text with random Seed",
    "Bjornulf_ShowText": "👁 Show (Text, Int, Float)",
    "Bjornulf_ImageMaskCutter": "🖼✂ Cut Image with Mask",
    "Bjornulf_LoadImageWithTransparency": "📥🖼 Load Image with Transparency ▢",
    "Bjornulf_CombineBackgroundOverlay": "🖼+🖼 Stack two images (Background+Overlay alpha)",
    "Bjornulf_GrayscaleTransform": "🖼➜🔲 Image to grayscale (black & white)",
    "Bjornulf_RemoveTransparency": "▢➜⬛ Remove image Transparency (alpha)",
    "Bjornulf_ResizeImage": "📏 Resize Image",
    "Bjornulf_ResizeImagePercentage": "📏 Resize Image Percentage",
    "Bjornulf_SaveImageToFolder": "💾🖼📁 Save Image(s) to a folder",
    "Bjornulf_SaveImageWithTextToFolder": "💾🖼📝📁 Save Image(s) with Text to a folder",
    "Bjornulf_SaveTmpImage": "💾🖼 Save Image (tmp_api.png) ⚠️💣",
    "Bjornulf_LoadTmpImage": "📥🖼 Load Image (tmp_api.png)",
    "Bjornulf_SaveText": "💾 Save Text",
    "Bjornulf_CombineTexts": "🔗 Combine (Texts)",
    "Bjornulf_imagesToVideo": "🖼➜📹 images to video (FFMPEG Save Video)",
    "Bjornulf_VideoPingPong": "📹 video PingPong",
    "Bjornulf_ollamaLoader": "🦙 Ollama (Description)",
    "Bjornulf_FreeVRAM": "🧹 Free VRAM hack",
    "Bjornulf_PickInput": "⏸️ Paused. Select input, Pick 👇",
    "Bjornulf_PauseResume": "⏸️ Paused. Resume / Stop / Basket 🧺, Pick 👇",
    "Bjornulf_LoadImagesFromSelectedFolder": "📥🖼📂 Load Images from output folder",
    "Bjornulf_SelectImageFromList": "🖼👈 Select an Image, Pick",
    "Bjornulf_IfElse": "🔀 If-Else (input / compare_with)",
    "Bjornulf_ImageDetails": "🖼🔍 Image Details",
    "Bjornulf_CombineImages": "🖼🔗 Combine Images",
}









WEB_DIRECTORY = "./web"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
