#lang sicp

(define (last-pair x)
  (if (null? (cdr x))
      x
      (last-pair (cdr x))))
(define (append! x y)
  (set-cdr! (last-pair x) y)
  x)

(define (member? x lst) 
  (cond ((null? lst) #f)
        ((eq? x (car lst)) #t)
        (else (member? x (cdr lst)))))

(define (contains-loop? x)
  (define (loop-inner x tracker)
    (cond ((null? x) #f)
          ((member? x tracker) #t)
          (else (loop-inner (cdr x) (append tracker (list x))))))
  (loop-inner x '()))

(define list1 '(a b c))
(contains-loop? list1)

(define list2 '(a b c))
(set-car! list2 (cdr list2))
(set-cdr! list2 (cddr list2))
(contains-loop? list2)

(define list3 '(a b c))
(set-car! (cdr list3) (cddr list3))
(set-car! list3 (cdr list3))
(contains-loop? list3)

;; No more infinite looping!
(define list4 '(a b c))
(set-cdr! (cddr list4) list4)
(contains-loop? list4)
