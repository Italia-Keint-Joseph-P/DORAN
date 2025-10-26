import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import Dataset

def load_qa_pairs(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conversations = []
    for item in data:
        question = item.get('question', '').strip()
        answer = item.get('answer', '').strip()
        if question and answer:
            # Format as conversational input: question + answer
            conversations.append({'text': question + " " + answer})
    return conversations

def tokenize_function(examples, tokenizer):
    return tokenizer(examples['text'], truncation=True, max_length=128)

def main():
    json_path = "database/faqs.json"  # Path to your JSON file with Q&A pairs
    model_name = "microsoft/DialoGPT-medium"
    output_dir = "./fine_tuned_dialoGPT"

    # Load data
    conversations = load_qa_pairs(json_path)
    dataset = Dataset.from_list(conversations)

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # Tokenize dataset
    tokenized_dataset = dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=500,
        save_total_limit=2,
        prediction_loss_only=True,
        logging_dir='./logs',
        logging_steps=100,
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=tokenized_dataset,
    )

    # Train model
    trainer.train()

    # Save model and tokenizer
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

if __name__ == "__main__":
    main()
