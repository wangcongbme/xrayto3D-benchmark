python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 8 --accelerator gpu --res 2.25 --model_name OneDConcat --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout
python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 4 --accelerator gpu --res 2.25 --model_name MultiScale2DPermuteConcat --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout
python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 8 --accelerator gpu --res 2.25 --model_name TwoDPermuteConcat --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout
python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 8 --accelerator gpu --res 2.25 --model_name AttentionUnet --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout
python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 8 --accelerator gpu --res 2.25 --model_name UNet --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout
python train.py  configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_train+val.csv configs/paths/totalsegmentator_hips/TotalSegmentor-hips-DRR-full_test.csv --gpu 0 --tags model-compare --size 128 --batch_size 8 --accelerator gpu --res 2.25 --model_name UNETR --epochs -1 --loss DiceLoss  --lr 0.002 --steps 3000 --dropout