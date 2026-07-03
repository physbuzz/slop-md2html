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

(define (count-pairs x)
  (define tracker (list 'first-element))
  (define (count-pairs-inner x tracker)
    (cond ((not (pair? x)) 0)
          ((member? x tracker) 0)
          (else (begin 
            (append! tracker (list x))
            (+ 1
               (count-pairs-inner (car x) tracker)
               (count-pairs-inner (cdr x) tracker))))))
  (count-pairs-inner x tracker))

(define list1 '(a b c))
(count-pairs list1)

(define list2 '(a b c))
(set-car! list2 (cdr list2))
(set-cdr! list2 (cddr list2))
(count-pairs list2)

(define list3 '(a b c))
(set-car! (cdr list3) (cddr list3))
(set-car! list3 (cdr list3))
(count-pairs list3)

;; No more infinite looping!
(define list4 '(a b c))
(set-cdr! (cddr list4) list4)
(count-pairs list4)
