```markdown
# Cont-Kukanov Smart Order Router Backtest

This repository implements a backtest and optimizer for the Cont & Kukanov static cost model for optimal order placement in fragmented limit order markets. The script splits a 5,000-share buy order across multiple venues to minimize execution costs, using the exact allocator logic from the provided pseudocode.

## Code Structure

- **backtest.py**: Loads `l1_day.csv`, processes L1 market data, implements the static allocator, and runs a 50-iteration parameter search for `lambda_over`, `lambda_under`, and `theta_queue`. It benchmarks the tuned result against three baselines: best-ask, TWAP (60s buckets), and VWAP (weighted by displayed ask size). Outputs a JSON summary and a bar chart (`results.png`).
- **allocator_pseudocode.txt**: The exact static allocation algorithm (do not modify).
- **l1_day.csv**: Mocked L1 market data for backtesting.
- **results.png/results.json**: Example output files (optional).

## Parameter Search

- Random search over:
    - `lambda_over`: [0.001, 0.005, 0.01, 0.05, 0.1]
    - `lambda_under`: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    - `theta_queue`: [0.0001, 0.0005, 0.001, 0.005, 0.01]
- Final candidates are verified deterministically.

## How to Run

```
pip install numpy pandas matplotlib
python backtest.py
```

## Output

- Prints a JSON object with the best parameters, total/average cost for optimal and baseline strategies, and savings in basis points.
- Saves a bar chart of average execution price as `results.png`.

## Suggested Improvement

To further improve fill realism, add queue position modeling using historical fill probabilities for each venue. This would allow the allocator to better estimate the likelihood of limit order fills and adjust allocations dynamically based on observed queue dynamics.

---

*Implementation strictly follows the provided pseudocode and assignment requirements. For details, see allocator_pseudocode.txt and the task description.*
```
This README is concise, covers code structure, parameter search, how to run, output, and your suggested improvement-meeting assignment requirements and ready to paste to GitHub.

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/51461689/ca0eaad0-66be-424b-96bf-94da5c3afda7/allocator_psuedocode.txt
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/51461689/090577f1-dffb-4999-875a-2bd071f0f63d/Trial-Task-Description.docx
[3] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/51461689/b0bd1e28-37b7-4099-a557-1e4bad61f166/Optimal-Order-Placement-in-Limit-Order-Markets.pdf
[4] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/51461689/21128fe1-40ba-4ec8-899d-c51ea2c16ea4/l1_day.csv
[5] https://en.wikipedia.org/wiki/Paris
[6] https://en.wikipedia.org/wiki/France
[7] https://home.adelphi.edu/~ca19535/page%204.html
[8] https://www.coe.int/en/web/interculturalcities/paris
[9] https://www.vedantu.com/question-answer/what-is-the-capital-of-france-class-9-social-science-cbse-617f85b4689fd62b59bc504c
[10] https://testbook.com/question-answer/which-is-the-capital-city-of-france--61c5718c1415c5341398033a
[11] https://www.britannica.com/place/Paris
[12] https://www.britannica.com/place/France
[13] https://multimedia.europarl.europa.eu/en/video/infoclip-european-union-capitals-paris-france_I199003

---
Answer from Perplexity: pplx.ai/share
