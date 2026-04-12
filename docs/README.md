---
title: Data Cleaning OpenEnv
emoji: 🧹
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
  - data-cleaning
  - reinforcement-learning
  - real-world
pinned: false
---

# 🧹 Data Cleaning OpenEnv

An OpenEnv-compliant environment where AI agents learn to clean messy tabular data — a task that consumes ~80% of real-world data science effort.

[![Demo](https://img.shields.io/badge/Demo-HuggingFace-yellow)](https://huggingface.co/spaces/Kylian07/Meta_env_rl)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🎯 Overview

This environment provides a standardized benchmark for training and evaluating AI agents on **real-world data cleaning tasks**. Unlike toy problems or games, this simulates actual work that data scientists perform daily.

### Why Data Cleaning?

- **Real-world relevance**: 80% of data science time is spent cleaning data
- **Clear objectives**: Deterministic right/wrong answers
- **Measurable progress**: Cell-by-cell scoring
- **Practical impact**: Automated data cleaning would save millions of work hours

## 🚀 Quick Start

### Try the Live Demo

Visit the deployed environment:
- **API**: https://kylian07-my-env.hf.space/
- **Docs**: https://kylian07-my-env.hf.space/docs

### Run Locally

```bash
# Clone the repository
https://github.com/Kylian07/my-openenv.git
cd data-cleaning-env

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
