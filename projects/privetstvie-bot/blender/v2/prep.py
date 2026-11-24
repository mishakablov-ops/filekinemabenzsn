# заливает фон референса ближайшим цветом героя, чтобы проекция не тащила серый фон на края
from PIL import Image
import numpy as np
from scipy import ndimage
for n in ('front','back'):
    a=np.asarray(Image.open('/mnt/project-files/aipollon/privetstvie-bot/ref3d/apollon-%s.png'%n).convert('RGB')).astype(float)
    bgrow=np.median(a[:, :60],axis=1); fg=np.abs(a-bgrow[:,None,:]).sum(-1)>45
    fg=ndimage.binary_opening(fg,iterations=2); fg[945:]=False   # отсечь тень пола
    fg=ndimage.binary_erosion(fg,iterations=2)
    idx=ndimage.distance_transform_edt(~fg,return_distances=False,return_indices=True)
    out=a[idx[0],idx[1]]
    Image.fromarray(out.astype('uint8')).save('/tmp/claude-0/v2/tex_%s.png'%n)
