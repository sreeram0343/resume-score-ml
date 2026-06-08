import React from 'react'
import './globals.css'
import type { Metadata, Viewport } from 'next'

export const metadata: Metadata = {
  title: 'Resume Score Checker & ATS Optimizer | AI Scorer',
  description: 'Maximize your hiring chances with an enterprise-grade AI Resume Scorer and ATS Optimizer powered by XGBoost & SHAP explanation.',
  keywords: 'ATS Optimizer, Resume Scorer, Resume Reviewer, Job Description Match, SHAP explainer, XGBoost, NLP Resume',
  authors: [{ name: 'DeepMind Antigravity' }],
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

