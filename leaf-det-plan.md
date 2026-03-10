
You are an expert computer vision engineer. Your task is to design and implement a complete **feature-based leaf-like structure detection system** using Python and OpenCV. The system must detect leaf-like shapes in images using classical computer vision techniques (no deep learning).

Your output must include a complete project structure, well-documented code, and clear reasoning for design choices.

---

# Objective

Build a robust pipeline that detects **leaf-like structures** from images or video frames using feature detection and contour analysis.

The system must work on natural images where leaves may appear in varying sizes, orientations, and lighting conditions.

Do NOT use neural networks, pretrained models, or deep learning libraries.

Use only:

* Python
* OpenCV
* NumPy
* Optional: Matplotlib for debugging

---

# Required Pipeline

Implement the following stages clearly and modularly.

## 1. Image Acquisition

Support:

* static images
* webcam video stream

Use configurable input paths.

---

## 2. Preprocessing

Implement a preprocessing module that includes:

* conversion to HSV and grayscale
* Gaussian blur
* optional green color masking
* noise reduction
* morphological operations (opening/closing)

Allow parameters to be configurable.

---

## 3. Edge Detection

Implement Canny edge detection with configurable thresholds.

The system should allow automatic threshold tuning experiments.

---

## 4. Contour Extraction

Extract contours using OpenCV.

Filter obvious noise using minimum area thresholds.

Return candidate contours.

---

## 5. Feature Extraction

For each contour compute the following geometric features:

* contour area
* perimeter
* bounding rectangle
* aspect ratio
* extent
* convex hull
* solidity
* circularity
* Hu moments

Store features in a structured format.

---

## 6. Leaf-like Shape Filtering

Design rule-based filters to identify leaf-like structures.

Typical characteristics:

* elongated shapes
* smooth convex boundaries
* moderate aspect ratios
* relatively high solidity

Implement configurable thresholds.

---

## 7. Optional Shape Matching

Add optional template-based matching using OpenCV shape matching functions.

Allow loading template leaf contours.

---

## 8. Detection Output

For detected leaf candidates:

* draw contour outlines
* draw bounding boxes
* label detected objects

Provide visual output.

---

# Project Structure

Generate a clean modular structure like:

leaf_detection_project/

data/
src/
tests/
results/

Inside src include modules for:

* preprocessing
* edge detection
* contour detection
* feature extraction
* filtering
* visualization
* main pipeline

Each module must be clean, reusable, and documented.

---

# Testing Framework

Provide:

1. Example script to test with multiple images
2. Batch testing capability
3. Metrics including:

   * number of contours
   * number of filtered candidates
   * processing time

---

# Parameter Tuning Tools

Implement helper utilities to allow easy tuning of:

* Canny thresholds
* contour area thresholds
* aspect ratio limits
* solidity thresholds

Include debugging visualizations to assist tuning.

---

# Code Quality Requirements

All code must:

* follow clean modular design
* include docstrings
* include comments explaining reasoning
* avoid monolithic scripts
* be easy to extend later

---

# Deliverables

Produce:

1. Complete Python codebase
2. Folder structure
3. Example usage instructions
4. Parameter tuning guidance
5. Suggestions for improving detection accuracy

---

# Important Constraints

Do not use deep learning.

Focus on classical computer vision techniques using OpenCV.

The system should prioritize robustness and explainability.

---

# Final Output

Provide:

* full implementation
* explanations of each module
* instructions for running the pipeline
* suggestions for improvements

Ensure the code can run immediately after installing dependencies.

Be thorough and professional in the implementation.
