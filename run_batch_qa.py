import json
from rag_module import get_rag_pipeline

def main() -> None:
    print("=== RUN BATCH QA START ===")

    # 1. Build RAG pipeline
    try:
        pipeline = get_rag_pipeline(use_scraped_data=True)
        print("Pipeline ready")
    except Exception as e:
        print(f"ERROR building pipeline: {e}")
        return

    # 2. Load questions
    try:
        with open("questions.txt", "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(questions)} questions")
    except FileNotFoundError:
        print("ERROR: questions.txt not found")
        return

    # 3. Ask each question and save incrementally
    results: list[dict] = []
    for i, q in enumerate(questions, start=1):
        try:
            print(f"[{i}/{len(questions)}] Q: {q}")
            ans = pipeline.answer_question(q)
            print(f"[{i}] A (first 120 chars): {str(ans)[:120]}...")
            results.append({"question": q, "answer": ans})
        except Exception as e:
            print(f"ERROR on question {i}: {e}")
            results.append({"question": q, "answer": f"ERROR: {e}"})

        # Save after each question
        with open("answers.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Done! answers.json written with {len(results)} entries.")
    print("=== RUN BATCH QA END ===")

if __name__ == "__main__":
    print("run_batch_qa.py executed as script")
    main()