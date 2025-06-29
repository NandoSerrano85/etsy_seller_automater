import cv2
import numpy as np

class MaskCreator:
    def __init__(self, mockup_image_path):
        # Class variables to maintain state
        self.drawing_layer = None
        self.static_layer = None
        self.instruction_overlay = None
        self.points = []
        self.drawing_mode = None
        self.rect_start = None
        self.scale_factor = 1.0
        self.max_display_size = 1200  # Maximum size for display
        self.mockup_image_path = mockup_image_path
        
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback function to handle drawing interactions."""
        print(f"Mouse Event - Type: {event}, X: {x}, Y: {y}")
        print(f"Current points: {self.points}")
        print(f"Drawing mode: {self.drawing_mode}")
        
        # Create a clean copy for drawing
        temp_layer = np.zeros_like(self.drawing_layer)
        
        if self.drawing_mode == 'point':
            # Point mode handling
            if event == cv2.EVENT_LBUTTONDOWN:
                self.points.append((x, y))
                print(f"Point added: ({x}, {y}). Total points: {len(self.points)}")
            
            # Draw all existing points and lines
            if self.points:
                # Draw points
                for i, point in enumerate(self.points):
                    cv2.circle(temp_layer, point, 5, (0, 255, 0), -1)  # Green filled circles
                    # Add point numbers
                    cv2.putText(temp_layer, str(i+1), (point[0]+8, point[1]-8), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Draw lines between points
                if len(self.points) > 1:
                    for i in range(1, len(self.points)):
                        cv2.line(temp_layer, self.points[i-1], self.points[i], (0, 255, 255), 2)
                
                # Draw line from last point to current position during mouse move
                if self.points and event == cv2.EVENT_MOUSEMOVE:
                    cv2.line(temp_layer, self.points[-1], (x, y), (0, 255, 255), 2)
        
        elif self.drawing_mode == 'rectangle':
            # Rectangle mode handling
            if event == cv2.EVENT_LBUTTONDOWN:
                self.rect_start = (x, y)
                self.points = []
                print(f"Rectangle start: ({x}, {y})")
            elif event == cv2.EVENT_LBUTTONUP and self.rect_start:
                # Create rectangle points
                self.points = [
                    self.rect_start,
                    (x, self.rect_start[1]),
                    (x, y),
                    (self.rect_start[0], y)
                ]
                print(f"Rectangle completed with points: {self.points}")
                self.rect_start = None
            elif event == cv2.EVENT_MOUSEMOVE and self.rect_start:
                # Draw preview rectangle
                cv2.rectangle(temp_layer, self.rect_start, (x, y), (0, 255, 255), 2)
        
        # Update drawing layer
        self.drawing_layer = temp_layer.copy()
        
        # Combine layers and display
        self.update_display()
    
    def update_display(self):
        """Update the display with current drawing state."""
        # Combine static layer and drawing layer
        result = cv2.addWeighted(self.static_layer, 1, self.drawing_layer, 1, 0)
        
        # Add instruction overlay using the improved method
        result_with_overlay = self.add_instruction_overlay(result)
        
        cv2.imshow('Image', result_with_overlay)
    
    def add_instruction_overlay(self, image):
        """
        Add semi-transparent overlay with instructions to the image
        """
        instructions = [
            "P: Point mode",
            "S: Rectangle mode",
            "C: Close/Create shape",
            "R: Reset",
            "Q: Quit"
        ]

        overlay = image.copy()
        height, width = image.shape[:2]
        
        # Adjusted font size and thickness for better visibility
        font_scale = 1.0
        thickness = 3
        padding = 20
        line_height = 60
        
        # Calculate overlay dimensions
        text_width = 300
        overlay_height = len(instructions) * line_height + 2 * padding
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Create solid black background with high opacity
        cv2.rectangle(overlay, (padding, padding), 
                     (text_width + padding, overlay_height),
                     (0, 0, 0), -1)  # Filled rectangle
        
        # Add instructions text with white outline for better visibility
        y = padding + line_height
        for text in instructions:
            # White outline
            cv2.putText(overlay, text, (padding + 5, y), font,
                       font_scale, (255, 255, 255), thickness + 2)
            # Black text
            cv2.putText(overlay, text, (padding + 5, y), font,
                       font_scale, (0, 0, 0), thickness)
            y += line_height
        
        # Create the final overlay with proper opacity
        result = image.copy()
        overlay_region = overlay[padding:overlay_height+padding, padding:text_width+padding*2]
        alpha = 0.85  # Increase opacity (0-1)
        
        # Blend only the overlay region
        cv2.addWeighted(
            overlay[padding:overlay_height+padding, padding:text_width+padding*2],
            alpha,
            result[padding:overlay_height+padding, padding:text_width+padding*2],
            1 - alpha,
            0,
            result[padding:overlay_height+padding, padding:text_width+padding*2]
        )
        
        return result
    
    def resize_for_display(self, image):
        """Resize image if too large for display"""
        height, width = image.shape[:2]
        if max(height, width) > self.max_display_size:
            scale = self.max_display_size / max(height, width)
            new_size = (int(width * scale), int(height * scale))
            return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return image
    
    def create_custom_mask(self):
        """Creates multiple custom masks by letting user draw polygon shapes or rectangles."""
        
        # Read and resize image for display
        img = cv2.imread(self.mockup_image_path[0], cv2.IMREAD_UNCHANGED)
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Get number of mask areas from user
        try:
            num_masks = int(input("How many mask areas do you want to create? (1-2): ").strip())
            if num_masks < 1 or num_masks > 2:
                print("Please enter 1 or 2 mask areas.")
                return None, None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None, None
        
        # Resize large images for better performance
        display_img = self.resize_for_display(img)
        self.scale_factor = img.shape[1] / display_img.shape[1]
        print(f"Scale factor: {self.scale_factor}")
        
        masks = []
        all_points = []
        
        for mask_num in range(num_masks):
            print(f"\n=== Creating mask {mask_num + 1} ===")
            print("Instructions:")
            print("- Press 'P' for point mode (click to add points)")
            print("- Press 'S' for rectangle mode (click and drag)")
            print("- Press 'C' to close shape and create mask (need 3+ points)")
            print("- Press 'R' to reset current shape")
            print("- Press 'Q' to quit")
            
            # Initialize state for current mask
            self.static_layer = display_img.copy()
            self.drawing_layer = np.zeros_like(display_img)
            self.points = []
            self.drawing_mode = None
            self.rect_start = None
            
            # Create window and set mouse callback
            cv2.namedWindow('Image', cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback('Image', self.mouse_callback)
            
            # Initial display
            self.update_display()
            
            # Main loop for the current mask
            mask_created = False
            while not mask_created:
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('p') or key == ord('P'):
                    self.drawing_mode = 'point'
                    self.points = []
                    self.rect_start = None
                    self.drawing_layer.fill(0)
                    print("Switched to point mode. Click to add points.")
                    
                elif key == ord('s') or key == ord('S'):
                    self.drawing_mode = 'rectangle'
                    self.points = []
                    self.rect_start = None
                    self.drawing_layer.fill(0)
                    print("Switched to rectangle mode. Click and drag to create rectangle.")
                    
                elif key == ord('c') or key == ord('C'):
                    if self.points and len(self.points) >= 3:
                        # Scale points back to original image size
                        scaled_points = [(int(x * self.scale_factor), int(y * self.scale_factor)) 
                                       for x, y in self.points]
                        
                        print(f"Creating mask with {len(scaled_points)} points:")
                        for i, point in enumerate(scaled_points):
                            print(f"  Point {i+1}: {point}")
                        
                        # Create mask
                        mask = np.zeros(img.shape[:2], dtype=np.uint8)
                        points_array = np.array([scaled_points], dtype=np.int32)
                        cv2.fillPoly(mask, points_array, 255)
                        
                        masks.append(mask.tolist())
                        all_points.append(scaled_points)
                        
                        print(f"Mask {mask_num + 1} created successfully!")
                        mask_created = True
                    else:
                        print(f"Need at least 3 points to create a mask. Current points: {len(self.points)}")
                        
                elif key == ord('r') or key == ord('R'):
                    self.points = []
                    self.rect_start = None
                    self.drawing_layer.fill(0)
                    self.update_display()
                    print("Shape reset. Start drawing again.")
                    
                elif key == ord('q') or key == ord('Q'):
                    print("Quitting mask creation.")
                    cv2.destroyAllWindows()
                    return None, None
        
        cv2.destroyAllWindows()
        
        print(f"\n=== Summary ===")
        print(f"Created {len(masks)} masks with the following points:")
        for i, points in enumerate(all_points):
            print(f"Mask {i+1}: {len(points)} points - {points}")
        
        return masks, all_points