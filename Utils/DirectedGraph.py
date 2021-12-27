from Utils.XAbleObject import SerializableObject
import copy


class DirectedGraph(SerializableObject):
    def __init__(self, V=None, A=None):
        """
        V->list of vertices  [x, y, ...]
                              0  1   
        A->list of adjacency [[...], [...], ...]
                                0      1     
        """
        if V:
            self.V = V
        else:
            self.V = []

        if A:
            self.A = A
        else:
            self.A = [[] for i in range(len(self.V))]

    def sort_verticies(self, key=lambda x: x, reverse=False):
        tmp = [(i, v, adj) for i, (v, adj) in enumerate(zip(self.V, self.A))]
        tmp.sort(key=lambda x: key(x[1]), reverse=reverse)
        old_to_new_indicies = dict([(e[0], i) for i, e in enumerate(tmp)])
        self.V = [e[1] for e in tmp]
        self.A = [[old_to_new_indicies[old_i] for old_i in e[2]] for e in tmp]

    def get_index(self, x):
        return self.V.index(x)

    def get_vertex(self, ix):
        return self.V[ix]

    def set_index(self, ix, value):
        self.V[ix] = value

    def set_vertex(self, x, value):
        ix = self.get_index(x)
        self.set_index(ix, value)

    def adjacent(self, x, y):
        ix = self.get_index(x)
        iy = self.get_index(y)

        return iy in self.A[ix]

    def neighbors(self, x):
        ix = self.get_index(x)

        return [self.V[i] for i in self.A[ix]]

    def in_neighbors(self, x):
        ix = self.get_index(x)
        n = []
        for (iy, adj) in enumerate(self.A):
            if ix in adj:
                n.append(self.V[iy])

        return n

    def unoriented_neighbors(self, x):
        neighbors = self.neighbors(x)
        return neighbors + [
            x for x in self.in_neighbors(x) if x not in neighbors
        ]

    def get_edge_number(self):
        return sum(map(len, self.A))

    def order(self):
        return len(self.V)

    def out_degree(self, x):
        ix = self.get_index(x)
        return len(self.A[ix])

    def in_degree(self, x):
        ix = self.get_index(x)
        d = 0
        for adj in self.A:
            if ix in adj:
                d += 1

        return d

    def add_vertex(self, x):
        if x not in self.V:
            self.V.append(x)
            self.A.append([])

    def add_vertices(self, verticies):
        for x in verticies:
            self.add_vertex(x)

    def remove_vertex(self, x):
        ix = self.get_index(x)
        for adj in self.A:
            try:
                adj.remove(ix)
            except:
                pass
            for i, iy in enumerate(adj):
                if iy > ix:
                    adj[i] -= 1

        del self.V[ix]
        del self.A[ix]

    def remove_verticies(self, verticies):
        for x in verticies:
            self.remove_vertex(x)

    def add_link(self, x, y, tag=None):
        ix = self.get_index(x)
        iy = self.get_index(y)

        if iy not in self.A[ix]:
            self.A[ix].append(iy)

    def add_links(self, links):
        for x, y in links:
            self.add_link(x, y)

    def remove_link(self, x, y):
        ix = self.get_index(x)
        iy = self.get_index(y)

        try:
            self.A[ix].remove(iy)
        except ValueError:
            pass

    def remove_links(self, links):
        for x, y in links:
            self.remove_link(x, y)

    def bfs(self):
        remainders = []
        if self.order() > 0:
            remainders.append(self.V[0])
        viewed = []

        while len(remainders) > 0:
            h = remainders.pop()
            if h not in viewed:
                viewed.append(h)
                for n in self.neighbors(h):
                    remainders.append(n)

        return viewed

    def is_connected(self):
        return len(self.bfs()) == self.order()

    def weak_bfs(self):
        remainders = []
        if self.order() > 0:
            remainders.append(self.V[0])
        viewed = []

        while len(remainders) > 0:
            h = remainders.pop()
            if h not in viewed:
                viewed.append(h)
                for n in self.unoriented_neighbors(h):
                    remainders.append(n)

        return viewed

    def is_weak_connected(self):
        return len(self.weak_bfs()) == self.order()

    def __getitem__(self, x):
        return self.A[self.get_index(x)]

    def __repr__(self):
        return repr(self.to_dict())

    def __str__(self):
        return str(self.to_dict())

    def copy(self):
        return DirectedGraph(self.V.copy(), copy.deepcopy(self.A))

    def to_dict(self):
        return super().to_dict(V=self.V, A=self.A)
