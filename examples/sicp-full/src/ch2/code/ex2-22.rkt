#lang sicp
(define (square x) (* x x))
(define (square-list items) (map square items))
(define (square-list-louis items)
  (define (iter things answer)
    (if (null? things)
        answer
        (iter (cdr things)
              (cons answer
                    (square 
                     (car things))))))
  (iter items nil))
(square-list (list 1 2 3 4))
(square-list-louis (list 1 2 3 4))
