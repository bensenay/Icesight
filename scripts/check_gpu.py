import torch

print("PyTorch version:", torch.__version__)
print("GPU available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("GPU count:", torch.cuda.device_count())

    x = torch.rand(1000, 1000, device="cuda")
    y = torch.rand(1000, 1000, device="cuda")
    z = x @ y

    print("GPU test passed:", z.shape)
else:
    print("GPU not detected")