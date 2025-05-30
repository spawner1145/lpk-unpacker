import sys
import os
import argparse
from Core.lpk_loader import *
from Core.utils import *

def main():
    parser = argparse.ArgumentParser(
        description="LPK文件解包器 - 支持Live2D标准目录结构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py model.lpk ./output
  python main.py -v -c config.json workshop_model.lpk ./output
  python main.py -vv model.lpk ./output  (调试模式)

输出目录结构:
  model_name/
  ├── model.model3.json    (主配置)
  ├── model.moc3          (模型数据)
  ├── textures/           (纹理文件)
  ├── motions/            (动作文件)
  │   ├── idle/           (待机动作)
  │   ├── tap/            (点击动作)
  │   ├── flick/          (滑动动作)
  │   └── pinch/          (捏取动作)
  ├── expressions/        (表情文件)
  ├── physics/            (物理文件)
  ├── pose/               (姿势文件)
  ├── effects/            (特效文件)
  ├── userdata/           (用户数据)
  ├── sounds/             (音频文件)
  └── 其他文件直接放在根目录
        """
    )
    parser.add_argument("-v", "--verbosity", action="count", default=0, 
                       help="增加输出详细度 (-v=信息, -vv=调试)")
    parser.add_argument("-c", "--config", 
                       help="config.json文件路径 (Steam Workshop文件需要)")
    parser.add_argument("target_lpk", 
                       help="要解包的LPK文件路径")
    parser.add_argument("output_dir", default='./output', nargs='?',
                       help="解包输出目录")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target_lpk):
        print(f"错误: LPK文件不存在: {args.target_lpk}")
        return 1
    
    if not args.target_lpk.lower().endswith('.lpk'):
        print(f"警告: 文件扩展名不是.lpk: {args.target_lpk}")
    
    if args.config and not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        return 1
    
    loglevels = ["ERROR", "INFO", "DEBUG"]
    verbosity = min(args.verbosity, len(loglevels) - 1)
    loglevel = loglevels[verbosity]
    
    logging.basicConfig(
        level=getattr(logging, loglevel),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("=" * 50)
    print("    LPK解包器 - Live2D标准目录结构")
    print("=" * 50)
    print(f"输入文件: {args.target_lpk}")
    print(f"输出目录: {args.output_dir}")
    if args.config:
        print(f"配置文件: {args.config}")
    print("=" * 50)
    
    try:
        loader = LpkLoader(args.target_lpk, args.config)
        loader.extract(args.output_dir)
        
        print("\n" + "=" * 50)
        print("    解包完成！")
        print("=" * 50)
        print(f"文件已解包到: {os.path.abspath(args.output_dir)}")
        print("\n目录结构已按Live2D标准组织:")
        print("  ├── textures/     (纹理文件)")
        print("  ├── motions/      (动作文件)")
        print("  │   ├── idle/     (待机动作)")
        print("  │   ├── tap/      (点击动作)")
        print("  │   ├── flick/    (滑动动作)")
        print("  │   └── pinch/    (捏取动作)")
        print("  ├── expressions/  (表情文件)")
        print("  ├── physics/      (物理文件)")
        print("  ├── pose/         (姿势文件)")
        print("  ├── effects/      (特效文件)")
        print("  ├── userdata/     (用户数据)")
        print("  ├── sounds/       (音频文件)")
        print("  └── 其他文件直接放在根目录")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"\n错误: 解包失败")
        print(f"原因: {str(e)}")
        if verbosity >= 2:
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
