from torch import nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, in_feats, out_feats, stride=1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_feats, out_feats, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_feats),
            nn.ReLU(),
            nn.Conv2d(out_feats, out_feats, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_feats),
        )
        self.downsample = nn.Sequential(
            nn.Conv2d(in_feats, out_feats, kernel_size=1, stride=stride, bias=False),
            nn.BatchNorm2d(out_feats),
        ) if stride != 1 else None

    def forward(self, x):
        y_out = self.net(x)
        x_out = x if self.downsample is None else self.downsample(x)
        out = F.relu(x_out + y_out)
        return out

class ResNet(nn.Module):
    def __init__(self, n_blocks_per_n_feats, n_outs=1000):
        super().__init__()
        in_feats0 = 64

        self.in_layers = nn.Sequential(
            nn.Conv2d(3, in_feats0, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(in_feats0),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
        )

        all_out_feats = [64, 128, 256, 512]
        all_in_feats = [in_feats0] + all_out_feats[:-1]
        strides = [1, 2, 2, 2]
        self.residual_layers = nn.Sequential(
            *(nn.Sequential(
                 ResidualBlock(in_feats, out_feats, stride),
                 *(ResidualBlock(out_feats, out_feats) for _ in range(n_blocks-1)),
             )
             for in_feats, out_feats, n_blocks, stride in
             zip(all_in_feats, all_out_feats, n_blocks_per_n_feats, strides))
        )

        self.out_layers = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(512, n_outs),
        )

    def forward(self, x):
        x = self.in_layers(x)
        x = self.residual_layers(x)
        x = self.out_layers(x)
        return x

def resnet34_with_pretrained_weights():
    simple_resnet34 = ResNet([3, 4, 6, 3])
    from torchvision import models
    torch_resnet34 = models.resnet34(pretrained=True)
    new_state_dict = {k1:v2 for (k1, _), (k2, v2) in zip(simple_resnet34.state_dict().items(), torch_resnet34.state_dict().items())}
    simple_resnet34.load_state_dict(new_state_dict)
    import torch
    x = torch.randn((5, 3, 224, 224))
    assert torch.allclose(simple_resnet34(x), torch_resnet34(x))
    return simple_resnet34
