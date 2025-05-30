# LPK UNPACKER

一个用于逆向LPK文件(一般来说是live2d的加密格式)的工具，特别针对Live2D模型文件(live2d viewerex里下载的)进行了优化，支持标准目录结构输出

- ✅ 支持标准LPK文件解包 (`STD2_0`类型)
- ✅ 支持Steam Workshop LPK文件(live 2d viewer ex)解包 (`STM_1_0`类型)
- ✅ 文件类型识别
- ✅ Live2D标准目录结构输出

## 系统要求

- Python 3.6+
- Windows/Linux/macOS

## 安装依赖

```bash
pip install filetype
```

## 使用方法

```bash
# 基本用法
python main.py model.lpk ./output

# 使用配置文件 (Steam Workshop文件需要)
python main.py -c config.json workshop_model.lpk ./output

# 详细输出模式
python main.py -v model.lpk ./output

# 调试模式
python main.py -vv model.lpk ./output
```

### 参数说明

- `target_lpk`: 要解包的LPK文件路径
- `output_dir`: 解包输出目录
- `-c, --config`: 配置文件路径 (Steam Workshop文件必需)
- `-v, --verbosity`: 增加输出详细度 (可重复使用: -v, -vv)

## 配置文件

对于Steam Workshop的LPK文件，需要提供配置文件 `config.json`:

```json
{
  "lpkFile": "example.lpk",
  "fileId": "123456789",
  "title": "角色名称或模型标题",
  "metaData": "example_metadata"
}
```

### 配置文件字段说明

- `fileId`: Steam Workshop文件ID (必需)
- `lpkFile`: LPK文件名 (必需)
- `metaData`: 元数据字符串 (必需)
- `title`: 模型标题 (可选，用作输出文件夹名称)

### 如何获取 fileId

Steam Workshop的fileId通常位于:
```
PATH_TO_STEAM/steamapps/common/Live2DViewerEX/shared/workshop/[数字文件夹名]
```
或者
```
PATH_TO_STEAM/steamapps/workshop/content/[数字文件夹名]
```
其中数字文件夹名就是fileId，lpk文件和config.json通常也在这两个文件夹里

## 输出文件夹命名规则

解包器会按以下优先级确定输出文件夹名称：

1. **config.json中的title字段** (如果存在且非空)
2. **LPK文件中的character字段** (如果存在且非空)  
3. **默认名称** (`character_1`, `character_2`等)

### 文件夹名称合法化

程序会自动处理文件夹名称中的特殊字符：
- 移除Windows不支持的字符: `< > : " / \ | ? *`
- 替换为下划线 `_`
- 移除开头和结尾的空格和点号
- 限制长度不超过100个字符

示例：
- `"角色名称/包含<特殊>字符"` → `"角色名称_包含_特殊_字符"`
- `"Touhou Cannonball - Tenshi Hinanawi"` → `"Touhou Cannonball - Tenshi Hinanawi"`

## 输出目录结构

解包后的文件将按照Live2D标准目录结构组织:

```
model_name/
├── model.model3.json          # 主模型配置文件
├── model.moc3                 # 模型数据文件
├── config.cfg                 # 其他配置文件 (直接放在根目录)
├── textures/                  # 纹理文件
│   ├── texture_00.png
│   └── texture_01.png
├── motions/                   # 动作文件
│   ├── idle/                  # 待机动作
│   │   └── idle_01.motion3.json
│   ├── tap/                   # 点击动作
│   │   └── tap_body.motion3.json
│   ├── flick/                 # 滑动动作
│   │   └── flick_01.motion3.json
│   └── pinch/                 # 捏取动作
│       └── pinch_01.motion3.json
├── expressions/               # 表情文件
│   ├── expression_01.exp3.json
│   └── expression_02.exp3.json
├── physics/                   # 物理文件
│   └── physics.physic3.json
├── pose/                      # 姿势文件
│   └── pose.json
├── effects/                   # 特效文件
│   └── effect.json
├── userdata/                  # 用户数据
│   └── userdata.json
└── sounds/                    # 音频文件
    └── voice.wav
```

## 文件分类规则

| 文件类型 | 目录 | 识别规则 |
|---------|------|----------|
| 纹理文件 | `textures/` | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tga` |
| 动作文件 | `motions/` | 包含"motion"的JSON文件 |
| 表情文件 | `expressions/` | 包含"expression"或"exp"的JSON文件 |
| 物理文件 | `physics/` | 包含"physics"的JSON文件 |
| 姿势文件 | `pose/` | 包含"pose"的JSON文件 |
| 特效文件 | `effects/` | 包含"effect"的JSON文件 |
| 用户数据 | `userdata/` | 包含"userdata"的JSON文件 |
| 音频文件 | `sounds/` | `.wav`, `.mp3`, `.ogg` |
| 模型核心 | 根目录 | `.moc3`, `.model3.json` |
| 其他文件 | 根目录 | 无法分类的文件直接放在根目录 |

## 动作文件子分类

动作文件会进一步按类型分类到子目录:

- `motions/idle/` - 待机动作 (包含"idle")
- `motions/tap/` - 点击动作 (包含"tap"或"touch") 
- `motions/flick/` - 滑动动作 (包含"flick")
- `motions/pinch/` - 捏取动作 (包含"pinch")

## 示例输出

```
解包完成！
输出目录: C:\output\character_name

目录结构符合Live2D标准:
  ├── textures/     (纹理文件)
  ├── motions/      (动作文件)
  │   ├── idle/     (待机动作)
  │   ├── tap/      (点击动作)
  │   ├── flick/    (滑动动作)
  │   └── pinch/    (捏取动作)
  ├── expressions/  (表情文件)
  ├── physics/      (物理文件)
  ├── pose/         (姿势文件)
  ├── effects/      (特效文件)
  ├── userdata/     (用户数据)
  ├── sounds/       (音频文件)
  └── 其他文件直接放在根目录
```


