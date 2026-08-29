from PIL import Image

from app.analysis import caption_analysis, hamming_distance, perceptual_hash


def test_caption_analysis_rewards_different_caption_vocabularies():
    repeated = caption_analysis(["a dog runs"] * 5)
    varied = caption_analysis(
        [
            "a dog runs through grass",
            "a puppy chases a ball",
            "an animal plays outdoors",
            "a brown dog leaps",
            "a pet runs fast",
        ]
    )
    assert repeated.disagreement_score == 0
    assert varied.disagreement_score > repeated.disagreement_score


def test_hamming_distance_counts_changed_bits():
    assert hamming_distance(0b1010, 0b1111) == 2


def test_perceptual_hash_is_an_eight_by_eight_average_hash():
    image = Image.new("L", (8, 8), 0)
    for x in range(4, 8):
        for y in range(8):
            image.putpixel((x, y), 255)
    assert perceptual_hash(image) == int("0f0f0f0f0f0f0f0f", 16)
