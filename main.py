import os
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Create DIR for docs
output_dir = "documents"
os.makedirs(output_dir, exist_ok=True)
'''
# Main doc A
doc_a = (
    "Python is a versatile programming language. It is widely used in data science, machine learning, and web development. With its extensive libraries and frameworks, Python enables developers to create robust applications quickly. In the realm of data science, Python is often favored for its simplicity and powerful tools like Pandas, NumPy, and Matplotlib. Machine learning engineers frequently rely on Python due to its support for frameworks such as TensorFlow, PyTorch, and Scikit-learn. Python is not only about data science or machine learning; it is also a go-to language for web development. Frameworks like Django and Flask allow developers to build scalable and secure web applications. Moreover, Python excels in scripting, automation, and even game development. The language's readability and community support make it an excellent choice for beginners and experts alike. From simple scripts to complex machine learning models, Python continues to expand its reach in the tech world. Its cross-platform nature and vast ecosystem ensure its place as a top choice for programmers worldwide."
)

# Docs to compare
docs = [
    (
        "Python is a popular programming language known for its versatility. It is widely used in areas like data science, web development, and automation. Developers appreciate Python for its extensive libraries and frameworks. In data science, tools like Pandas and NumPy make Python a powerful choice for analysis and modeling."
    ),
    (
        "Machine learning and AI often rely on Python due to its simplicity and vast ecosystem. With frameworks like TensorFlow and PyTorch, Python enables rapid prototyping and deployment of machine learning models. It is also a favorite for research in artificial intelligence."
    ),
    (
        "Web development with Python is made easy using frameworks like Django and Flask. These tools allow developers to build robust and scalable web applications. Python's syntax makes it a preferred choice for both backend development and APIs."
    ),
    (
        "Data science heavily relies on Python for its tools and simplicity. Libraries like Matplotlib and Seaborn are used for data visualization, while Pandas and NumPy handle data manipulation and analysis. Python's ecosystem continues to grow with innovations in the field."
    ),
    (
        "Python is not just about data science or web development. It is also widely used for scripting and automation tasks. From automating mundane tasks to creating deployment scripts, Python's versatility shines. Its readability makes it an excellent choice."
    )
]

# Save doc A
with open(os.path.join(output_dir, "A.txt"), "w", encoding="utf-8") as f:
    f.write(doc_a)

# Save other docs
for i, doc in enumerate(docs):
    with open(os.path.join(output_dir, f"Doc_{chr(66+i)}.txt"), "w", encoding="utf-8") as f:
        f.write(doc)

print(f"Documents generated in '{output_dir}' folder.")
'''
# Function to calculate similarity
def calculate_similarity():
    # Load model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Read docs
    file_paths = [os.path.join(output_dir, file) for file in os.listdir(output_dir)]

    with open(file_paths[0], "r", encoding="utf-8") as f:
        main_sentences = f.read().split(". ")

    helper_sentences = []
    for path in file_paths[1:]:
        with open(path, "r", encoding="utf-8") as f:
            helper_sentences.extend(f.read().split(". "))

    # Compute embeddings
    main_embeddings = model.encode(main_sentences, convert_to_tensor=True)
    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    #Calculate sentence similarities
    results = []
    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        max_sim = np.max(similarities.numpy())
        results.append((main_sentences[i], max_sim))

    return results

results = calculate_similarity()

def generate_report(results, output_file="report.html"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<html><body>")
        for sentence, score in results:
            if score > 0.8:
                f.write(f"<p style='color:green;'>Covered: {sentence}</p>")
            elif score < 0.4:
                f.write(f"<p style='color:red;'>Uncovered: {sentence}</p>")
            else:
                f.write(f"<p style='color:orange;'>Problematic: {sentence}</p>")
        f.write("</body></html>")
    print(f"Report saved to {output_file}")

generate_report(results)
