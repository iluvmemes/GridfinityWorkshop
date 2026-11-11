"""Package exported lid/label STLs with color names and swatches."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workshop.lid_export import package
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--lid-color',default='grey');parser.add_argument('--label-color',default='white')
    args=parser.parse_args();print(package(args.folder.resolve(),lid_color=args.lid_color,label_color=args.label_color))
