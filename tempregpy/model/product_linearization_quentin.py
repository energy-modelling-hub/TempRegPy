import logging
from ortools.math_opt.python import mathopt
import numpy as np
from scipy.spatial import ConvexHull

logger = logging.getLogger(__name__)

def list_faces_from_N(N, method='triangles'):
    faces = []
    eps = 1e-3/N
    # first, assume 'polygons' method
    # later, split the squares into triangles if 'triangles' method
    for j in range(2*N):
        for k in range(2*N):
            x = (j-k)/(2*N) + 0.5
            y = (j+k+1)/(2*N) - 0.5
            if (x>=0) and (x<=1) and (y>=0) and (y<=1):
                pts = []
                for delta in [(-1,0),(0,-1),(1,0),(0,1)]:
                        xx = x + delta[0]/(2*N)
                        yy = y + delta[-1]/(2*N)
                        if (xx>=0-eps) and (xx<=1+eps) and (yy>=0-eps) and (yy<=1+eps):
                            pts.append([xx,yy,xx*yy])
                pts = np.array(pts)
                faces.append(pts)
    if method=='triangles':
        faces_triang=[]
        for face in faces:
            if len(face)==3:
                faces_triang.append(face)
            else:
                x,y = face.mean(axis=0)[0:2]
                if (y>=x - eps) ^ (x+y>=1-eps):
                    face = face[face[:,0].argsort(),:]
                else:
                    face = face[face[:,1].argsort(),:]
                faces_triang.append(face[0:3,:])
                faces_triang.append(face[1:4,:])
        faces = list(faces_triang)
    return faces

def equations_from_faces_3d(faces):
    list_coeffs = []
    list_equations = []
    for face in faces:
        # find the linear coeffs
        # only keep 3 points to calculate linear coeff
        M = face[:3,:]*1
        M[:,2] = 1.
        Z = face[:3,2]*1
        # coeffs = (a,b,c) in z = a*x + b*y + c
        coeffs = np.linalg.solve(M,Z)
        list_coeffs.append(coeffs)
        # find the domain inequalities
        hull_2d = ConvexHull(face[:,:2])
        list_equations.append(hull_2d.equations)
        
    return list_coeffs, list_equations


def equations_sum_convex(N):
    list_coeffs_j = []
    list_equations_j = []
    list_coeffs_k = []
    list_equations_k = []
    for j in range(2*N):
        tmp_eq = []
        if j>0:
            tmp_eq.append([-1,-1,j/N])
        if j<2*N-1:
            tmp_eq.append([1,1,-(j+1)/N])
        tmp_eq = np.array(tmp_eq)
        list_equations_j.append(tmp_eq)
        a = (j+1)/(2*N) - 0.5
        b = j/(2*N) + 0.5
        c = -j*(j+1)/(4*N**2) + 0.25
        list_coeffs_j.append(np.array([a,b,c]))
    for k in range(2*N):
        tmp_eq = []
        if k<2*N-1:
            tmp_eq.append([-1,1,1-(k+1)/N])
        if k>0:
            tmp_eq.append([1,-1,-1+k/N])
        tmp_eq = np.array(tmp_eq)
        list_equations_k.append(tmp_eq)
        a = k/(2*N)
        b = -k/(2*N)
        c = k*(k+1)/(4*N**2) - (2*k+1)/(4*N)
        list_coeffs_k.append(np.array([a,b,c]))
    return list_coeffs_j, list_equations_j, list_coeffs_k, list_equations_k


def do_mathopt_quentin_product_linearization(
    model: mathopt.Model,
    partition_method: str,
    N: int,
    X_var,
    Y_var,
    Z_var
):
    # logger.info(f"Performing {partition_method} product linearization for variables: "
                # f"{X_var.name}, {Y_var.name}, {Z_var.name}")
    
    if partition_method not in ['triangles','polygons','sum of convex']:
        raise ValueError(f"Invalid method: {partition_method}. "
                         "Supported methods are 'triangles', 'polygons', and 'sum of convex'.")
    
    x = model.add_variable(
        name=f"{X_var.name}_aux",
        lb=0.0,
        ub=1.0,
    )

    y = model.add_variable(
        name=f"{Y_var.name}_aux",
        lb=0.0,
        ub=1.0
    )

    z = model.add_variable(
        name=f"{Z_var.name}_aux",
        lb=0.0,
        ub=1.0
    )

    z_c = []
    xx = []
    yy = []
    zz = []
    bv = []

    X_min = X_var.lower_bound
    X_max = X_var.upper_bound
    Y_min = Y_var.lower_bound
    Y_max = Y_var.upper_bound

    model.add_linear_constraint(
        X_var == X_min + (X_max - X_min) * x,
        name = f"X_{Z_var.name}_normalization",
    )

    model.add_linear_constraint(
        Y_var == Y_min + (Y_max - Y_min) * y,
        name = f"Y_{Z_var.name}_normalization",
    )

    model.add_linear_constraint(
        Z_var == X_min * Y_min + Y_min * (X_max - X_min) * x +
                X_min * (Y_max - Y_min) * y + (Y_max - Y_min) * (X_max - X_min) * z,
        name=f"Z_{Z_var.name}_normalization"
    )
    
    if partition_method in ['triangles','polygons']:
        N_C = 1
        # get polygons/triangles faces
        faces = list_faces_from_N(N, method=partition_method)
        # get linear coeffs and region inequalities
        list_coeffs, list_equations = equations_from_faces_3d(faces)
        COEFFS = [list_coeffs]
        EQUATIONS = [list_equations]
    else:
        N_C = 2
        # get linear coeffs and region inequalities
        list_coeffs_j, list_equations_j, list_coeffs_k, list_equations_k = equations_sum_convex(N)
        COEFFS = [list_coeffs_j, list_coeffs_k]
        EQUATIONS = [list_equations_j, list_equations_k]

    z_c = [model.add_variable(name=f"z_c({Z_var.name},{cc})") for cc in range(N_C)]
    # z = zc_1 + zc_2
    model.add_linear_constraint(z == sum(z_c), name=f"sum_convex({X_var.name},{Y_var.name})")

    for cc in range(N_C):
        coeffs_ = list(COEFFS[cc])
        equations_ = list(EQUATIONS[cc])

        # number of regions
        NN = len(equations_)

        # define regional components of x, y, z
        xx_c = [model.add_variable(name=f"xx_{X_var.name}_{cc}_{i}", lb=0.0, ub=1.0) for i in range(NN)]
        yy_c = [model.add_variable(name=f"yy_{Y_var.name}_{cc}_{i}", lb=0.0, ub=1.0) for i in range(NN)]
        zz_c = [model.add_variable(name=f"zz_{Z_var.name}_{cc}_{i}") for i in range(NN)]
        # binary variable indicating which region is active
        bv_c = [model.add_binary_variable(name=f"bv_{Z_var.name}_{cc}_{i}") for i in range(NN)]

        # append the regional variables to the overall lists
        xx.append(xx_c)
        yy.append(yy_c)
        zz.append(zz_c)
        bv.append(bv_c)

        # x, y, z are equal to the sum of their components
        model.add_linear_constraint(x == sum(xx_c), name=f"sum_xx_{Z_var.name}_{cc}")
        model.add_linear_constraint(y == sum(yy_c), name=f"sum_yy_{Z_var.name}_{cc}")
        model.add_linear_constraint(z_c[cc] == sum(zz_c), name=f"sum_zz_{Z_var.name}_{cc}")
        # only one region can be active at a time
        model.add_linear_constraint(sum(bv_c) == 1.0, name=f"sum_bv_{Z_var.name}_{cc}")

        for i in range(NN):
            a, b, c = coeffs_[i]
            # relationship between x, y, z on a given region
            model.add_linear_constraint(zz_c[i] == a * xx_c[i] + b * yy_c[i] + c * bv_c[i],
                                          name=f"rel_{Z_var.name}_{cc}_{i}")
            # if a region is not active, the coordinates of the component are forced to 0
            model.add_linear_constraint(xx_c[i] <= bv_c[i], name=f"xx_bound_{Z_var.name}_{cc}_{i}")
            model.add_linear_constraint(yy_c[i] <= bv_c[i], name=f"yy_bound_{Z_var.name}_{cc}_{i}")
            for j in range(len(equations_[i])):
                aa, bb, cc_coef = equations_[i][j]
                # inequalities defining the region
                model.add_linear_constraint(aa * xx_c[i] + bb * yy_c[i] + cc_coef * bv_c[i] <= 0.0,
                                              name=f"ineq_{Z_var.name}_{cc}_{i}_{j}")

    variables = {
        'X': X_var, 'Y': Y_var, 'Z': Z_var,
        'x': x, 'y': y, 'z': z,
        'xx': xx, 'yy': yy, 'zz': zz,
        'z_c': z_c, 'bv': bv
    }