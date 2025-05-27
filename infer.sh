for i in $(seq 1 15)
do
  formatted_value=$(printf "%06d" $i)
  python fpack_generate_video.py \
    --dit /mnt/cfs_yanfa/models/framepack_h1111/FramePackI2V_HY_bf16.safetensors \
    --vae /mnt/cfs_yanfa/models/framepack_h1111/pytorch_model.pt \
    --text_encoder1 /mnt/cfs_yanfa/models/hunyuanvideo-community/HunyuanVideo/text_encoder/model-00001-of-00004.safetensors \
    --text_encoder2 /mnt/cfs_yanfa/models/hunyuanvideo-community/HunyuanVideo/text_encoder_2/model.safetensors \
    --image_encoder /mnt/cfs_yanfa/models/framepack_h1111/model.safetensors \
    --image_path /mnt/cfs_yanfa/lisongru/Projects/musubi-tuner/data/girl.png \
    --prompt "小女孩伸手从纸箱中拿出了一只duck-wang, duck-wang再她手上摇晃脑袋" \
    --video_size 464 832 --video_seconds 5 --fps 16 --infer_steps 25 \
    --attn_mode sdpa --fp8_scaled \
    --vae_chunk_size 32 --vae_spatial_tile_sample_min_size 128 \
    --save_path /mnt/cfs_yanfa/lisongru/Projects/musubi-tuner/data/$i --output_type both \
    --seed 1234 --lora_multiplier 1.0 --lora_weight /mnt/cfs_yanfa/lisongru/Projects/musubi-tuner/outputs/test1-${formatted_value}.safetensors
done
