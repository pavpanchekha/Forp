class Cons(object):
    def __init__(self, car=None, cdr=None):
        self.car = car
        self.cdr = cdr

    def __repr__(self):
        return "(" + " ".join(map(repr, self.__list__())) + ")"

    def __len__(self):
        l = 0
        while self is not None:
            l += 1
            self = self.cdr
        return l

    def __list__(self):
        l = []
        while self is not None:
            l.append(self.car)
            self = self.cdr
        return l

    def __getitem__(self, n):
        if isinstance(n, int):
            cell = self
            while n:
                n -= 1
                cell = cell.cdr
            return cell.car
        elif isinstance(n, slice):
            res = []
            i = 0

            curr = self
            while i < slice.start:
                curr = curr.cdr
                i += 1
            while i < slice.end:
                j = 0
                while j < slice.step:
                    curr = curr.cdr
                    j += 1
                res.append(curr.car)
                i += 1 + j
            return res
        else:
            raise TypeError("Cons does not support nonintegral indices")
