from typing import Optional


# Stores pipe tile definitions and helper lookups.
# To add a new pipe type, just add an entry to PIPE_MAP.
class PipeConfig:
    PIPE_MAP: dict[str, list[tuple[int, int]]] = {
        '|': [(0, -1), (0, 1)],
        '-': [(1, 0), (-1, 0)],
        'L': [(0, -1), (1, 0)],
        'J': [(0, -1), (-1, 0)],
        '7': [(0, 1), (-1, 0)],
        'F': [(0, 1), (1, 0)],
        '.': [],
        'S': [(0, -1), (0, 1), (1, 0), (-1, 0)],
    }

    # Pipes that count as a crossing in the ray-casting algorithm
    VERTICAL_CROSSING = {'|', 'L', 'J'}

    @classmethod
    def directions(cls, char: str) -> list[tuple[int, int]]:
        return cls.PIPE_MAP.get(char, [])

    @classmethod
    def char_for_directions(cls, dirs: list[tuple[int, int]]) -> Optional[str]:
        for char, d in cls.PIPE_MAP.items():
            if d == dirs:
                return char
        return None


# Parses the raw input and provides read/write access to grid cells.
class Grid:
    def __init__(self, raw: str):
        self._grid: list[list[str]] = [
            list(row) for row in raw.strip().split('\n')
        ]
        self.height = len(self._grid)
        self.width = len(self._grid[0])

    def get(self, x: int, y: int) -> str:
        return self._grid[y][x]

    def set(self, x: int, y: int, char: str) -> None:
        self._grid[y][x] = char

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def find_char(self, char: str) -> Optional[tuple[int, int]]:
        for y, row in enumerate(self._grid):
            for x, c in enumerate(row):
                if c == char:
                    return (x, y)
        return None

    def rows(self):
        return range(self.height)

    def cols(self):
        return range(self.width)


# Resolves valid moves from a given position based on pipe connectivity.
# Optionally excludes the direction we just came from to avoid backtracking.
class MoveResolver:
    OPPOSITE = {(0, -1): (0, 1), (0, 1): (0, -1), (1, 0): (-1, 0), (-1, 0): (1, 0)}

    def __init__(self, grid: Grid, config: PipeConfig):
        self._grid = grid
        self._config = config

    def valid_moves(
        self,
        pos: tuple[int, int],
        prev_dir: Optional[tuple[int, int]] = None,
    ) -> list[tuple[int, int]]:
        x, y = pos
        char = self._grid.get(x, y)
        moves = []

        for d in self._config.directions(char):
            nx, ny = x + d[0], y + d[1]
            if not self._grid.in_bounds(nx, ny):
                continue
            neighbor_char = self._grid.get(nx, ny)
            back = self.OPPOSITE.get(d)
            if back in self._config.directions(neighbor_char) and prev_dir != back:
                moves.append((nx, ny))

        return moves


# Determines the actual pipe character at the start position
# by looking at which neighbors connect back to it.
class StartCharResolver:
    def __init__(self, move_resolver: MoveResolver, config: PipeConfig):
        self._resolver = move_resolver
        self._config = config

    def resolve(self, pos: tuple[int, int]) -> Optional[str]:
        moves = self._resolver.valid_moves(pos)
        dirs = [(mx - pos[0], my - pos[1]) for mx, my in moves]
        return self._config.char_for_directions(dirs)


# Iteratively walks the loop starting from a given position
# and returns the set of all tiles that belong to it.
class LoopTracer:
    def __init__(self, move_resolver: MoveResolver):
        self._resolver = move_resolver

    def trace(self, start: tuple[int, int]) -> set[tuple[int, int]]:
        visited: set[tuple[int, int]] = {start}
        pos = start
        prev_dir = None

        while True:
            moves = self._resolver.valid_moves(pos, prev_dir)
            if not moves:
                break
            nxt = moves[0]
            if nxt == start and len(visited) > 1:
                break
            visited.add(nxt)
            prev_dir = (nxt[0] - pos[0], nxt[1] - pos[1])
            pos = nxt

        return visited


# Counts tiles enclosed by the loop using the ray-casting algorithm:
# scan each row left to right, toggling inside/outside on vertical crossings.
class EnclosedAreaCounter:
    def __init__(self, grid: Grid, config: PipeConfig):
        self._grid = grid
        self._config = config

    def count(self, loop: set[tuple[int, int]]) -> int:
        total = 0
        for y in self._grid.rows():
            within = False
            for x in self._grid.cols():
                if (x, y) in loop:
                    if self._grid.get(x, y) in self._config.VERTICAL_CROSSING:
                        within = not within
                elif within:
                    total += 1
        return total


# Top-level solver: wires up all components and exposes part1/part2 answers.
class PipeMazeSolver:
    def __init__(self, raw_input: str):
        self._grid = Grid(raw_input)
        self._config = PipeConfig()
        self._move_resolver = MoveResolver(self._grid, self._config)
        self._start_resolver = StartCharResolver(self._move_resolver, self._config)
        self._tracer = LoopTracer(self._move_resolver)
        self._area_counter = EnclosedAreaCounter(self._grid, self._config)

        # Replace 'S' with its actual pipe character before solving
        start = self._grid.find_char('S')
        if start is None:
            raise ValueError("Start position 'S' not found in grid")
        self._start = start
        real_char = self._start_resolver.resolve(start)
        if real_char is None:
            raise ValueError("Could not determine start pipe character")
        self._grid.set(start[0], start[1], real_char)

    def part1(self) -> int:
        loop = self._tracer.trace(self._start)
        return len(loop) // 2

    def part2(self) -> int:
        loop = self._tracer.trace(self._start)
        return self._area_counter.count(loop)


if __name__ == '__main__':
    with open('puzzle_input.txt') as f:
        raw = f.read().strip()

    solver = PipeMazeSolver(raw)
    print('Part 1:', solver.part1())
    print('Part 2:', solver.part2())