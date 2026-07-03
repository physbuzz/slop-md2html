#lang sicp

;ch2 assoc
(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

;4.4.4.8 definitions
(define (make-binding variable value)
  (cons variable value))
(define (binding-variable binding)
  (car binding))
(define (binding-value binding)
  (cdr binding))
(define (binding-in-frame variable frame)
  (assoc variable frame))
(define (extend variable value frame)
  (cons (make-binding variable value) frame))

(define frame1 (extend '(? x) 'a '()))
(define frame2 (extend '(? y) 'b frame1))

frame2

(binding-in-frame '(? x) frame2)

(binding-in-frame '(? y) frame2)

(extend '(? x) 'b frame2)
