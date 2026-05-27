// struct_point.mc — Struct definition and member access
// Tests: struct definition, struct variables, member access with '.', struct as param

struct Point {
    int x;
    int y;
};

/* Compute the Manhattan distance between two points */
int manhattan(struct Point a, struct Point b) {
    int dx = a.x - b.x;
    int dy = a.y - b.y;

    // Absolute value of dx
    if (dx < 0) {
        dx = -dx;
    }
    // Absolute value of dy
    if (dy < 0) {
        dy = -dy;
    }

    return dx + dy;
}

/* Create a point translated by (dx, dy) */
struct Point translate(struct Point p, int dx, int dy) {
    struct Point result;
    result.x = p.x + dx;
    result.y = p.y + dy;
    return result;
}

int main() {
    struct Point p1;
    p1.x = 3;
    p1.y = 4;

    struct Point p2;
    p2.x = 7;
    p2.y = 1;

    int dist = manhattan(p1, p2);     // |3-7| + |4-1| = 4 + 3 = 7

    struct Point p3 = translate(p1, 10, 20);
    // p3.x = 13, p3.y = 24

    return dist;
}
