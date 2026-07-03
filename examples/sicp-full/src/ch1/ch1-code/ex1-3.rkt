#lang sicp

(define (mymin2 a b) (if (< a b) a b))
(define (mymin3 a b c) (mymin2 a (mymin2 b c)))
(define (largesquare a b c) (+ (* a a) (* b b) (* c c) (- (* (mymin3 a b c) (mymin3 a b c)))))

#| 
; A more typical solution to this problem is:
(define (f1 a b c)
  (if (< a b)
      (if (< a c)
          (+ (* b b) (* c c))
          (+ (* b b) (* a a)))
      (if (< b c)
          (+ (* a a) (* c c))
          (+ (* a a) (* b b)))))
|#

(largesquare 1 2 3)
