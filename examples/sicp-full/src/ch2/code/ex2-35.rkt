#lang sicp

(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))

;; The first two empty slots just implement a summation
;; The last empty slot is just the tree
;; The third slot is the complicated thing.
(define (count-leaves t)
  (accumulate (lambda (x y) (+ x y)) 0 
    (map 
      (lambda (s) 
        (if (pair? s) (count-leaves s) 1)) t)))

(define x (cons (list 1 2) (list 3 4)))
(count-leaves (list x x (list x x)))
