def export_results_to_csv(results, filepath):
    with open(filepath, 'w') as f:
        f.write('student,score,status\n')
        for r in results:
            f.write(f\"{r['name']},{r['score']},{r['passed']}\n\")
