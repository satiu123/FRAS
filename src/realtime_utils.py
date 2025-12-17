# 实时签到工具函数
import cv2

def draw_faces_with_names(frame, faces, results):
    """
    在图像上绘制人脸框和识别结果
    
    Args:
        frame: 原始图像 (BGR)
        faces: insightface 检测到的 face 对象列表
        results: 列表，每个元素为 (name, similarity, can_record)
    
    Returns:
        带标注的图像
    """
    img = frame.copy()
    for i, face in enumerate(faces):
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        
        name, sim, can_record = results[i]
        
        # 设置颜色：已签到（绿色），可签到（蓝色），未知（红色）
        if name == "Unknown":
            color = (0, 0, 255)  # 红色
        elif can_record:
            color = (255, 0, 0)  # 蓝色（即将签到）
        else:
            color = (0, 255, 0)  # 绿色（已签到，冷却中）
        
        # 画框
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # 写名字和相似度
        label = f"{name} ({sim:.2f})"
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return img