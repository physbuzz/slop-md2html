#lang sicp


; returns a+|b| by performing a+b if b>0, else a-b.
(define (a-plus-abs-b a b)
  ((if (> b 0) + -) a b))

(a-plus-abs-b 1 -3)
(a-plus-abs-b 1 3)
