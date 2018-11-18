from collections import Counter
import pytest
import pandas as pd

from tmclass_solutions.language_detector import wikipedia_language
from tmclass_solutions.language_detector import split_paragraphs
from tmclass_solutions.language_detector import make_language_detector_dataset
from tmclass_solutions.data_download import download_wikipedia_scraping_result
from tmclass_solutions.data_download import download_wikipedia_language_dataset
from tmclass_solutions import DATA_FOLDER_PATH

WIKIPEDIA_SCRAPING_ROOT = DATA_FOLDER_PATH / "wikipedia_scraping"


def setup():
    """Download the tests files if needed."""
    download_wikipedia_scraping_result()
    download_wikipedia_language_dataset()


def test_wikipedia_language():
    assert wikipedia_language("/path/to/it.wikipedia.org/wiki/Roma") == "it"
    assert wikipedia_language("azb.wikipedia.org") == "azb"
    assert wikipedia_language("fr.wikipedia.org/wiki/Portail:Accueil") == "fr"

    with pytest.raises(ValueError) as excinfo:
        wikipedia_language("/home/ogrisel")

    expected_message = "/home/ogrisel has no Wikipedia language information"
    assert str(excinfo.value) == expected_message


MULTI_PARAGRAPH_DOCUMENT = """\

This is the first paragraph. Is it not very interesting but it is the first
paragraph in the document.

And here is the second paragraph. It is much more interesting. This is the
second paragraph. This paragraph is very repetitive. This paragraph is very
repetitive. This paragraph is very repetitive. This paragraph is very
repetitive.

To short a paragraph.

This the third valid paragraph. It's boring but at least it's the final
paragraph.

"""

SHORT_DOCUMENT = "This is a very short document. It has only one line."


def test_split_paragraph_30():
    paragraphs = split_paragraphs(SHORT_DOCUMENT, min_length=30)
    assert len(paragraphs) == 1
    assert paragraphs[0] == SHORT_DOCUMENT

    paragraphs = split_paragraphs(MULTI_PARAGRAPH_DOCUMENT, min_length=30)
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("This is the first paragraph.")
    assert paragraphs[0].endswith("first\nparagraph in the document.")
    assert paragraphs[1].startswith("And here is the second paragraph.")
    assert paragraphs[1].endswith("very\nrepetitive.")
    assert paragraphs[2].startswith("This the third valid paragraph.")
    assert paragraphs[2].endswith("final\nparagraph.")
    assert all(len(p) > 30 for p in paragraphs)


def test_split_paragraph_100():
    paragraphs = split_paragraphs(SHORT_DOCUMENT, min_length=100)
    assert len(paragraphs) == 0
    paragraphs = split_paragraphs(MULTI_PARAGRAPH_DOCUMENT, min_length=100)
    assert len(paragraphs) == 2
    assert paragraphs[0].startswith("This is the first paragraph.")
    assert paragraphs[0].endswith("first\nparagraph in the document.")
    assert paragraphs[1].startswith("And here is the second paragraph.")
    assert paragraphs[1].endswith("very\nrepetitive.")


def test_language_detector_dataset():
    html_filepaths = list(WIKIPEDIA_SCRAPING_ROOT.glob("**/body"))
    html_filepaths = sorted(html_filepaths)

    texts, language_labels, article_names = make_language_detector_dataset(
        html_filepaths, min_length=30)

    assert len(texts) == len(language_labels) == len(article_names)
    assert len(texts) >= 10000

    text_lengths = [len(text) for text in texts]
    assert min(text_lengths) >= 30
    assert max(text_lengths) <= 10000

    assert article_names[0] == "أدب"
    assert language_labels[0] == "ar"

    assert article_names[-1] == "音乐"
    assert language_labels[-1] == "zh"

    # Check that our 29 different languages are represented
    label_counts = Counter(language_labels)
    assert len(label_counts) == 29

    # Check that all the classes are well represented and none is overly
    # represented.
    for label, count in label_counts.items():
        assert count >= 100, label
        assert count <= 1500, label

    label, count = label_counts.most_common(n=1)[0]
    assert label == "fr"
    assert count >= 1000

    # Convert the resulting python lists to the columns of a pandas dataframe
    # so as to save the resulting dataset as a parquet file which is a very
    # efficient and fast way to store heterogeneously typed tabulare data
    # sets.

    # dataset = pd.DataFrame({
    #     "article_name": article_names,
    #     "language": language_labels,
    #     "text": texts,
    # })
    # dataset.to_parquet(DATA_FOLDER_PATH / "wikipedia_language.parquet")