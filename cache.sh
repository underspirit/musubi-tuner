# data/i2v/i2v.toml
config_file=$1
cache_model=$2

function cache_vae() {
    python fpack_cache_latents.py \
        --dataset_config $config_file \
        --vae /mnt/cfs_yanfa/models/framepack_h1111/pytorch_model.pt \
        --image_encoder /mnt/cfs_yanfa/models/framepack_h1111/model.safetensors \
        --vae_chunk_size 32 \
        --latent_window_size 9 \
        --vae_spatial_tile_sample_min_size 128
}

function cache_text_encoder() {
    python fpack_cache_text_encoder_outputs.py \
        --dataset_config $config_file \
        --text_encoder1 /mnt/cfs_yanfa/models/hunyuanvideo-community/HunyuanVideo/text_encoder/model-00001-of-00004.safetensors \
        --text_encoder2 /mnt/cfs_yanfa/models/hunyuanvideo-community/HunyuanVideo/text_encoder_2/model.safetensors \
        --batch_size 16
}

if [ "$cache_model" == "vae" ]; then
    echo "Caching VAE"
    cache_vae
elif [ "$cache_model" == "text" ]; then
    echo "Caching text encoder"
    cache_text_encoder
elif [ "$cache_model" == "all" ]; then  
    echo "Caching VAE and text encoder"
    cache_vae
    cache_text_encoder
else
    echo "Invalid cache model: $cache_model"
    exit 1
fi
