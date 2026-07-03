#lang sicp
(define (make-monitored func)
  (let ((ncalls 0))
    (lambda (arg) 
      (cond ((eq? arg 'how-many-calls?) ncalls)
            ((eq? arg 'reset-count) (set! ncalls 0))
            (else (begin
              (set! ncalls (+ ncalls 1))
              (func arg)))))))

(define s (make-monitored sqrt))

(s 100)
(s 9)

(s 'how-many-calls?)
(s 'reset-count)
(s 'how-many-calls?)

