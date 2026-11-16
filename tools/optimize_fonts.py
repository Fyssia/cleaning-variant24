from pathlib import Path
import json,subprocess
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib.instancer import instantiateVariableFont
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'static/fonts';out.mkdir(parents=True,exist_ok=True)
source=Path(subprocess.check_output(['fc-match','-f','%{file}','Noto Sans'],text=True));audit=[]
for weight in [400,600,700]:
 font=TTFont(source)
 if 'fvar' in font:
  axes={axis.axisTag:(weight if axis.axisTag=='wght' else axis.defaultValue) for axis in font['fvar'].axes};font=instantiateVariableFont(font,axes,inplace=True)
 options=subset.Options();sub=subset.Subsetter(options=options);sub.populate(unicodes=[*range(0x0000,0x0250),*range(0x0400,0x0530),*range(0x2000,0x2070),0x20BD,0x20AC]);sub.subset(font);font.flavor='woff2';dest=out/f'noto-sans-{weight}.woff2';tmp=dest.with_suffix('.tmp');font.save(tmp);tmp.replace(dest);audit.append(dict(weight=weight,file=dest.name,bytes=dest.stat().st_size))
(ROOT/'evidence/fonts.json').write_text(json.dumps(audit,indent=2));print(audit)
