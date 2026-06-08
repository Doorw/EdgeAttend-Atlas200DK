import os
import torch
import torch.onnx
from model import CANNet


ONNX_PATH = "cannet.onnx"
CKPT_PATH = "model_best.pth.tar"


def clean_state_dict(state_dict):
    """
    兼容 DataParallel 训练保存的权重。
    如果 key 前面有 module.，这里会去掉。
    """
    new_state_dict = {}

    for key, value in state_dict.items():
        if key.startswith("module."):
            new_key = key[len("module."):]
        else:
            new_key = key
        new_state_dict[new_key] = value

    return new_state_dict


def main():
    if not os.path.exists(CKPT_PATH):
        raise FileNotFoundError(f"找不到权重文件：{CKPT_PATH}")

    # ONNX 导出建议用 CPU，更稳定，不依赖 CUDA
    device = torch.device("cpu")

    print("Step 1: 构建 CANNet 模型")

    # 注意：这里用 load_weights=True，避免再次下载 VGG16 预训练权重
    # 因为后面会直接加载 model_best.pth.tar
    model = CANNet(load_weights=True)

    print("Step 2: 加载训练好的权重")
    checkpoint = torch.load(CKPT_PATH, map_location=device)

    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint

    state_dict = clean_state_dict(state_dict)
    model.load_state_dict(state_dict, strict=True)

    model.to(device)
    model.eval()

    print("Step 3: 构造 ONNX 输入")

    # 推荐使用 384x384，避免 AdaptiveAvgPool2d 导出到 ONNX 时尺寸不整除报错
    dummy_input = torch.randn(1, 3, 384, 384, device=device)

    with torch.no_grad():
        output = model(dummy_input)
        print("模型输出尺寸：", tuple(output.shape))

    print("Step 4: 导出 ONNX")

    torch.onnx.export(
        model,
        dummy_input,
        ONNX_PATH,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["density_map"],
        dynamic_axes=None,
        verbose=False
    )

    print(f"ONNX 导出成功：{ONNX_PATH}")


if __name__ == "__main__":
    main()