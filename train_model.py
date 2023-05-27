from model import SQLIModel
model = SQLIModel()
model.train_model('sqli.csv', 'sqli_model.h5', 'tokenizer.pickle')
