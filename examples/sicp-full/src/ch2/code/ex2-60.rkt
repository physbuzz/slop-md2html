#lang sicp

(define (element-of-set? x set)
  (cond ((null? set) false)
        ((equal? x (car set)) true)
        (else (element-of-set? x (cdr set)))))

; Theta(1)
(define (adjoin-set x set)
  (cons x set))
  
;; Theta(n^2)
(define (intersection-set set1 set2)
  (cond ((or (null? set1) (null? set2)) 
         '())
        ((element-of-set? (car set1) set2)
         (cons (car set1)
               (intersection-set (cdr set1) 
                                 set2)))
        (else (intersection-set (cdr set1) 
                                set2))))

;; Theta(1) (or, if append is implemented with (length gset1) calls to cons, it's Theta(n))
(define (union-set gset1 gset2)
  (append gset1 gset2))

(define set1 '(a b c d e f))
(define set2 '(c d e f g h i))

(intersection-set set1 set2)
(union-set set1 set2)

