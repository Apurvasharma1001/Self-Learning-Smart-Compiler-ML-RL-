# 🧠 Self-Learning Smart Compiler (ML + RL)

A complete end-to-end compiler for a C-like language (Mini-C) with intelligent optimization selection powered by Machine Learning and Reinforcement Learning.

## ✨ Features

### 🔹 Compiler Core
- Full compilation pipeline
- PLY-based lexer and parser
- Three Address Code (TAC)
- Pseudo-assembly generation

### 🔹 Smart Optimization
- Constant Folding
- Dead Code Elimination
- CSE
- Copy Propagation
- LICM

- ML (Random Forest)
- RL (Q-Learning)

### 🔹 Modes
- Normal
- ML
- RL

## 🏗️ Architecture

Source → Lexer → Parser → AST → TAC → Optimizer → Codegen

## 🤖 ML/RL Overview

- ML predicts best optimization
- RL learns from reward
- Reward based on instruction reduction

## 📊 Results

- Up to 90% instruction reduction
- Efficient optimization selection

## 🛠️ Tech Stack

- Python
- PLY
- scikit-learn
- Flask

## 📌 Conclusion

Adaptive optimization improves compiler performance over static methods.
