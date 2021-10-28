from tkinter.filedialog import askopenfilenames
import pandas as pd

if __name__ == '__main__':
    all_files = askopenfilenames(title='Choose Files')
    final_dataframe = pd.DataFrame({"index": ["Fruit Factor"]})
    count = 1
    for fruit_files in all_files:
        data = pd.read_csv(fruit_files)
        fruit_factor = data.at['fruit_factor', 1]
        text = "name_of_file" + str(count)
        final_dataframe.insert(1, text, [fruit_factor], True)
        count += 1
    print(final_dataframe)
    final_dataframe.to_csv('quicky.csv', index=False)