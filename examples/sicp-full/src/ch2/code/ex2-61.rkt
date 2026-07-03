#lang sicp

(define (adjoin-set x set)
  (cond ((null? set) (list x))
        ((> x (car set)) 
         (cons (car set) (adjoin-set x (cdr set))))
        ((= x (car set)) set)
        (else (cons x set))))

(define set0 (list 0 4 8 12))

(adjoin-set 4 set0)
(adjoin-set 5 set0)
(adjoin-set 1 set0)
(adjoin-set -1 set0)
(adjoin-set 16 set0)
