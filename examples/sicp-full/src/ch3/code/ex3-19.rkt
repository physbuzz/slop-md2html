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
  ;; Checks if we can cdr x n times
  (define (try-step x n)
    (cond ((= n 0) x)
          ((not (pair? x)) #f)
          (else (try-step (cdr x) (- n 1)))))
  (define (loop-inner x y)
    (let ((xnew (try-step x 1))
          (ynew (try-step y 2)))
      (cond ((or (not ynew) (not xnew)) #f)
            ((eq? xnew ynew) #t)
            (else (loop-inner xnew ynew)))))
  (loop-inner x x))

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
