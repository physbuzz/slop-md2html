#lang sicp

; invariants: 
;   x and y together contain all original elements of x
;   y contains elements of the original x in reversed order
;   
(define (mystery x)
  (define (loop x y)
    (if (null? x)
        y
        (let ((temp (cdr x)))
          (set-cdr! x y)
          (loop temp x))))
  (loop x '()))

(define v (list 'a 'b 'c 'd))
(define w (mystery v))

w
v
