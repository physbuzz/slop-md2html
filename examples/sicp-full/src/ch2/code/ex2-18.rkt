#lang sicp

; reverse(a b c ... z) = (reverse(b c ... z) a) = (z reverse(a b ... y))
;; This works, but it's going to be god-awful slow!!! :(
(define (last-elem lst) 
  (if (null? (cdr lst)) (car lst) (last-elem (cdr lst))))
(define (most lst) 
  (if (null? (cdr lst)) nil (cons (car lst) (most (cdr lst)))))
(define (reverse-n2 lst)
  (if (null? lst) nil (cons (last-elem lst) (reverse-n2 (most lst)))))

;; This works and is much faster. Reversing a linked list naturally 
;; wants to use tail recursion!
(define (reverse lst)
  (define (reverse-help lst ret)
    (if (null? lst) 
      ret 
     (reverse-help (cdr lst) 
		   (cons (car lst) ret))))
  (reverse-help lst nil))

;; Let's test both versions
(display (reverse (list 1 2 3 4 5 6)))
(newline)
(display (reverse (list 1 2)))
(newline)
(display (reverse (list 1 )))
(newline)
(display (reverse (list)))
(newline)
(display (reverse-n2 (list 1 2 3 4 5 6)))
(newline)
(display (reverse-n2 (list 1 2)))
(newline)
(display (reverse-n2 (list 1 )))
(newline)
(display (reverse-n2 (list)))
(newline)
