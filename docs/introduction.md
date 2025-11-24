# Introduction

The **Pairwise Ranking System** is a modern Python application designed to help teams prioritize requirements, tasks, or features. Instead of assigning arbitrary numbers or t-shirt sizes, users compare items in pairs. This method is often more accurate and easier for humans to perform.

## The Problem
Prioritizing a long list of requirements is difficult.
- **Absolute scoring** (e.g., 1-10) is subjective and prone to bias.
- **Sorting** a list manually becomes unmanageable as the list grows ($O(n \log n)$ complexity).

## The Solution
This system uses **Active Bayesian Ranking** to efficiently determine the relative importance of items.
- **Pairwise Comparisons**: "Is A more valuable than B?" is an easier question than "How valuable is A on a scale of 1-10?".
- **Two Dimensions**: Rank items separately by **Business Value** and **Technical Complexity**.
- **Efficiency**: The system intelligently selects the next pair to compare, maximizing information gain and reducing the total number of votes needed.

## Key Features
- **Smart Ranking Algorithm**: Uses a TrueSkill-like Bayesian model with uncertainty sampling.
- **Visual Results**: View items on a Value vs. Complexity scatter plot.
- **Modern UI**: A clean, dark-themed web interface.
- **Persistence**: Automatically saves progress; resume anytime.
- **Docker Support**: Easy to deploy and run anywhere.
