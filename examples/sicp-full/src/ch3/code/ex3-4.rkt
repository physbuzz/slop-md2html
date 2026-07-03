#lang sicp
(define (make-account balance pw)
  (let ((num-consec-fails 0))
    (define (withdraw amount)
      (if (>= balance amount)
        (begin (set! balance
                 (- balance amount))
          balance)
        "Insufficient funds"))
    (define (deposit amount)
      (set! balance (+ balance amount))
      balance)
    (define (call-the-cops) 
      (display ">:( cops called") (newline))
    (define (return-errorfunc) 
      (begin 
        (set! num-consec-fails (+ num-consec-fails 1))
        (if (> num-consec-fails 7)
          (begin (call-the-cops)
                 (lambda args "N/A"))
          (lambda args "Incorrect Password"))))
    (define (dispatch pw-arg m)
      (if (not (eq? pw pw-arg)) 
        (return-errorfunc)
        (begin 
          (set! num-consec-fails 0)
          (cond 
            ((eq? m 'withdraw) withdraw)
            ((eq? m 'deposit) deposit)
            (else (error "Unknown request:
                         MAKE-ACCOUNT" m))))))
    dispatch))

(define acc 
  (make-account 100 'secret-password))

((acc 'secret-password 'withdraw) 40)
;60

((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
((acc 'some-other-password 'deposit) 50)
;"Incorrect password"


