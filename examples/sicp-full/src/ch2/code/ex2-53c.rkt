#lang sicp

(define (@@ f lst) 
  (cons f (cdr lst)))

(@@ 'g '(f x y))
