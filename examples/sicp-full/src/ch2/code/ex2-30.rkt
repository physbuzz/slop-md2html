#lang sicp

(define (square x) (* x x))
(define (square-tree tree)
  (cond ((null? tree) tree)
        ((not (pair? tree)) (square tree))
        (else (cons (square-tree (car tree)) 
                    (square-tree (cdr tree))))))

(define (square-tree-map tree)
  (if (not (pair? tree)) 
    (square tree)
    (map square-tree-map tree)))

(define examp (list 1 2 
                (list (list 3 4 5) 
                      (list 7 8 9) 
                      (list (list 10 11))) 
                (list 12 13)))
(square-tree examp)
(square-tree-map examp)
