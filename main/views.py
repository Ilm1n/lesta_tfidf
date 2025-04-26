import json, math, re
from collections import Counter, defaultdict

from django.shortcuts import render
from django.core.paginator import Paginator

from .forms import UploadFileForm


def split_into_documents(text: str):
    """
    Делит текст на "документы":
    - Если в тексте >=3 абзацев (по `\n\n`), возвращает их как документы.
    - Иначе группирует каждые 4 непустые строки в один документ.
    Убирает пустые строки.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) >= 3:
        return paragraphs

    documents = []
    temp = []
    for idx, line in enumerate(lines, start=1):
        temp.append(line)
        if idx % 4 == 0:
            documents.append(" ".join(temp))
            temp = []
    if temp:
        documents.append(" ".join(temp))
    return documents


def analyze_text(documents: list[str]):
    """
    Принимает список документов, возвращает список слов с tf, idf.
    """
    N = len(documents)
    tf_counts = Counter()
    for doc in documents:
        words = re.findall(r"\b\w+\b", doc.lower())
        tf_counts.update(words)

    df = defaultdict(int)
    for w in tf_counts:
        for doc in documents:
            if re.search(rf"\b{re.escape(w)}\b", doc.lower()):
                df[w] += 1

    results = []
    for w, tf in tf_counts.items():
        idf = math.log((N + 1) / (1 + df[w])) + 1
        results.append({"word": w, "tf": tf, "idf": round(idf, 6)})
    return results


def upload_text(request):
    form = UploadFileForm(request.POST or None, request.FILES or None)
    sort_order = request.GET.get("sort_order", "desc")

    if request.method == "POST" and form.is_valid():
        raw = request.FILES["file"].read().decode("utf-8", errors="ignore")
        documents = split_into_documents(raw)
        request.session["doc_count"] = len(documents)

        data = analyze_text(documents)

        if sort_order == "asc":
            data.sort(key=lambda x: x["idf"], reverse=False)
        else:
            data.sort(key=lambda x: x["idf"], reverse=True)

        data = data[:50]

        request.session["tfidf_data"] = json.dumps(data)

    stored = request.session.get("tfidf_data")
    data = json.loads(stored) if stored else []
    doc_count = request.session.get("doc_count", 0)

    if data:
        if sort_order == "asc":
            data.sort(key=lambda x: x["idf"], reverse=False)
        else:
            data.sort(key=lambda x: x["idf"], reverse=True)

    paginator = Paginator(data, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "form": form,
        "page_obj": page_obj,
        "doc_count": doc_count,
        "sort_order": sort_order,
    }
    return render(request, "main/upload.html", context)
