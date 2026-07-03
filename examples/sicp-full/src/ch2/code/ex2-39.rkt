#lang sicp
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
(define fold-right accumulate)
(define (fold-left op initial sequence)
  (define (iter result rest)
    (if (null? rest)
        result
        (iter (op result (car rest))
              (cdr rest))))
  (iter initial sequence))

(define (reverse1 sequence)
  (fold-right 
   (lambda (x y) (append y (list x))) nil sequence))

(define (reverse2 sequence)
  (fold-left 
   (lambda (x y) (cons y x)) nil sequence))

(reverse1 '(1 2 3 4 5))
(reverse2 '(1 2 3 4 5))
