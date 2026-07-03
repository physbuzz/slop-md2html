#lang sicp

(define (element-of-set? x set)
  (cond ((null? set) false)
        ((equal? x (car set)) true)
        (else (element-of-set? x (cdr set)))))

(define (adjoin-set x set)
  (if (element-of-set? x set)
      set
      (cons x set)))

(define (intersection-set set1 set2)
  (cond ((or (null? set1) (null? set2)) 
         '())
        ((element-of-set? (car set1) set2)
         (cons (car set1)
               (intersection-set (cdr set1) 
                                 set2)))
        (else (intersection-set (cdr set1) 
                                set2))))
(define (union-set gset1 gset2)
  (define (union-set-helper set1 set2 ret)
    (cond ((and (null? set1) (null? set2)) ret)
        ((null? set1) (union-set-helper set2 set1 ret))
        (else (if (element-of-set? (car set1) ret)
                  (union-set-helper (cdr set1) set2 ret)
                  (union-set-helper (cdr set1) set2 (cons (car set1) ret))))))
  (union-set-helper gset1 gset2 '()))

(define set1 '(a b c d e f))
(define set2 '(c d e f g h i))

(intersection-set set1 set2)
(union-set set1 set2)

