#lang sicp

(list 'a 'b 'c)
;; (a b c)

(list (list 'george))
;; ((george))

(cdr '((x1 x2) (y1 y2)))
;; ((y1 y2)), a list with one element '(y1 y2)

(cadr '((x1 x2) (y1 y2)))
;; (y1 y2), the car of the previous result

(pair? (car '(a short list)))
;; false, (car '(a short list)) is just 'a

(memq 'red '((red shoes) (blue socks)))
;; false, 'red is not a member of the list, '(red shoes) is.

(memq 'red '(red shoes blue socks))
;; (red shoes blue socks), the element is found so memq returns the list 
;; after and including 'red.



